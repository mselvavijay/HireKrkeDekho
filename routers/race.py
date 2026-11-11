import os
import json
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import time
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database import get_db
from models.models import UserProfile, RaceAttempt, RaceAnswer, RaceWinner, RaceDailyQuiz
from services.auth_token_service import get_current_user_from_header, get_optional_user_from_header
from services.race_service import contest_date, create_daily_quiz, decide_winner, get_cached_quiz, get_cached_quiz_questions, leaderboard, now_ist, public_name, questions_for_player, QUESTION_SECONDS, GRACE_SECONDS

router = APIRouter(prefix="/race", tags=["AI Race"])
IST = timezone(timedelta(hours=5, minutes=30))

RACE_ENABLED = os.getenv("RACE_ENABLED", "0").strip() == "1"
RACE_ADMIN_SECRET = os.getenv("RACE_ADMIN_SECRET", "")

def _race_required():
    if not RACE_ENABLED:
        raise HTTPException(status_code=503, detail="AI Race is currently disabled.")
ADMIN_EMAILS = {email.strip().lower() for email in os.getenv("ADMIN_EMAILS", "").split(",") if email.strip()}

_ADMIN_RATE_LIMIT_STORE = defaultdict(list)
_ADMIN_RATE_LIMIT = 30
_ADMIN_RATE_WINDOW = 60
class AnswerRequest(BaseModel): question_index: int = Field(ge=0, le=14); option_index: int = Field(ge=-1, le=3)
class DisplayNameRequest(BaseModel): display_name: str

def user_from_token(token, db):
    if not token or not isinstance(token, dict):
        return None
    user = db.query(UserProfile).filter_by(id=token.get("user_id"), email=token.get("email")).first()
    if not user:
        raise HTTPException(401, "Sign in with Google to continue.")
    return user

def require_admin(token):
    if not token or not isinstance(token, dict):
        raise HTTPException(401, "Admin sign-in required.")
    if not ADMIN_EMAILS or token.get("email", "").lower() not in ADMIN_EMAILS:
        raise HTTPException(403, "Admin access required.")

@router.get("/today")
async def today(db: Session = Depends(get_db), token=Depends(get_optional_user_from_header)):
    _race_required()
    user = user_from_token(token, db) if token else None
    day = contest_date()
    quiz = await create_daily_quiz(db, day)
    if quiz is None:
        raise HTTPException(status_code=503, detail="Quiz not ready, try again soon.")
    attempt = db.query(RaceAttempt).filter_by(contest_date=day, user_id=user.id).first() if user else None
    if attempt and attempt.status != "completed":
        max_sec = (QUESTION_SECONDS + GRACE_SECONDS) * 15 + 30
        created_at = attempt.created_at or attempt.question_started_at or now_ist()
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=IST)
        if (now_ist() - created_at).total_seconds() > max_sec:
            attempt.status = "completed"
            attempt.completed_at = now_ist()
            db.commit()
    return {
        "contest_date": day,
        "theme": quiz.theme,
        "question_count": 15,
        "seconds_per_question": QUESTION_SECONDS,
        "grace_seconds": GRACE_SECONDS,
        "attempt_status": attempt.status if attempt else "not_started",
        "leaderboard": leaderboard(db, day)[:10],
        "authenticated": user is not None,
        "user_email": user.email if user else None
    }

@router.post("/start")
async def start(db: Session = Depends(get_db), token=Depends(get_current_user_from_header)):
    _race_required()
    user = user_from_token(token, db); day = contest_date(); quiz = await create_daily_quiz(db, day)
    if quiz is None:
        raise HTTPException(status_code=503, detail="Quiz not ready, try again soon.")
    attempt = db.query(RaceAttempt).filter_by(contest_date=day, user_id=user.id).first()
    if attempt:
        max_sec = (QUESTION_SECONDS + GRACE_SECONDS) * 15 + 30
        created_at = attempt.created_at or attempt.question_started_at or now_ist()
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=IST)
        if attempt.status == "completed" or (now_ist() - created_at).total_seconds() > max_sec or attempt.current_question >= 15:
            if attempt.status != "completed":
                attempt.status = "completed"
                attempt.completed_at = now_ist()
                db.commit()
            raise HTTPException(409, "You have already completed todays contest.")
    if not attempt:
        name = public_name(getattr(user, "display_name", None) or (user.email or "").split("@")[0])
        attempt = RaceAttempt(contest_date=day, user_id=user.id, display_name=name, status="in_progress", current_question=0, question_started_at=now_ist())
        db.add(attempt); db.commit(); db.refresh(attempt)
    return {"attempt_id": attempt.id, "questions": questions_for_player(quiz), "current_question": attempt.current_question, "expires_in_seconds": QUESTION_SECONDS + GRACE_SECONDS}

@router.post("/admin/pregenerate")
async def pregenerate_quiz(x_admin_secret: str = Header(default=""), db: Session = Depends(get_db), token=Depends(get_current_user_from_header)):
    if not RACE_ADMIN_SECRET:
        raise HTTPException(status_code=503, detail="Pre-generation not configured.")
    if not x_admin_secret or x_admin_secret != RACE_ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Invalid admin secret.")
    _race_required()
    user = user_from_token(token, db)
    require_admin(token)
    from datetime import timedelta
    tomorrow = (now_ist() + timedelta(days=1)).date().isoformat()
    quiz = await create_daily_quiz(db, tomorrow)
    if quiz is None:
        raise HTTPException(status_code=503, detail="Quiz not ready, try again soon.")
    return {"contest_date": tomorrow, "theme": quiz.theme, "questions_generated": len(__import__("json").loads(quiz.questions_json))}


@router.post("/answer")
def answer(payload: AnswerRequest, db: Session = Depends(get_db), token=Depends(get_current_user_from_header)):
    _race_required()
    user = user_from_token(token, db)
    day = contest_date()
    attempt = db.query(RaceAttempt).filter_by(contest_date=day, user_id=user.id).first()
    if not attempt:
        raise HTTPException(409, "No active contest attempt.")
    if attempt.status == "completed":
        return {"correct": None, "completed": True, "score": attempt.score, "next_question": attempt.current_question}

    # If this question was already answered / recorded (e.g. duplicate network request or retry)
    if payload.question_index < attempt.current_question:
        return {"correct": None, "completed": attempt.status == "completed", "score": attempt.score, "next_question": attempt.current_question}

    # Check if an answer for this question was already recorded for this attempt
    existing_answer = db.query(RaceAnswer).filter_by(attempt_id=attempt.id, question_index=payload.question_index).first()
    if existing_answer:
        return {"correct": bool(existing_answer.is_correct), "completed": attempt.status == "completed", "score": attempt.score, "next_question": attempt.current_question}

    # If client jumped ahead (e.g. intermediate question missed / timed out), backfill missed questions safely
    if payload.question_index > attempt.current_question:
        while attempt.current_question < payload.question_index and attempt.current_question < 15:
            missed_idx = attempt.current_question
            prior = db.query(RaceAnswer).filter_by(attempt_id=attempt.id, question_index=missed_idx).first()
            if not prior:
                db.add(RaceAnswer(
                    attempt_id=attempt.id,
                    question_index=missed_idx,
                    selected_index=-1,
                    is_correct=0,
                    elapsed_ms=(QUESTION_SECONDS + GRACE_SECONDS) * 1000,
                ))
            attempt.total_time_ms += (QUESTION_SECONDS + GRACE_SECONDS) * 1000
            attempt.current_question += 1

    # Check if backfilling brought the attempt to completion
    if attempt.current_question >= 15:
        attempt.status = "completed"
        attempt.completed_at = now_ist()
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
        return {"correct": None, "completed": True, "score": attempt.score, "next_question": attempt.current_question}

    started_at = attempt.question_started_at or now_ist()
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=IST)
    elapsed = max(0, int((now_ist() - started_at).total_seconds() * 1000))

    questions = get_cached_quiz_questions(db, day)
    if not questions:
        quiz = db.query(RaceDailyQuiz).filter_by(contest_date=day).first()
        if quiz and quiz.questions_json:
            try:
                import json as _json
                questions = _json.loads(quiz.questions_json)
            except Exception:
                pass
    if not questions:
        raise HTTPException(status_code=503, detail="Today's quiz is unavailable. Please restart the contest.")
    if payload.question_index >= len(questions):
        raise HTTPException(status_code=409, detail="That question is unavailable.")
    question = questions[payload.question_index]
    correct = (
        elapsed <= (QUESTION_SECONDS + GRACE_SECONDS) * 1000
        and payload.option_index >= 0
        and payload.option_index == question.get("answer_index")
    )

    # Double check before adding answer to prevent unique constraint violation
    existing_curr = db.query(RaceAnswer).filter_by(attempt_id=attempt.id, question_index=payload.question_index).first()
    if not existing_curr:
        db.add(RaceAnswer(
            attempt_id=attempt.id,
            question_index=payload.question_index,
            selected_index=payload.option_index,
            is_correct=int(correct),
            elapsed_ms=elapsed,
        ))
        attempt.score += int(correct)
        attempt.total_time_ms += min(elapsed, (QUESTION_SECONDS + GRACE_SECONDS) * 1000)

    attempt.current_question = payload.question_index + 1
    if attempt.current_question >= 15:
        attempt.status = "completed"
        attempt.completed_at = now_ist()
    else:
        attempt.question_started_at = now_ist()
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        # Do not expose database internals, but always return JSON rather than an HTML 500 page.
        raise HTTPException(status_code=503, detail="Unable to save your answer. Please try again.")
    return {"correct": None, "completed": attempt.status == "completed", "score": attempt.score, "next_question": attempt.current_question}

@router.get("/leaderboard")
def board(db: Session = Depends(get_db)):
    return {"contest_date": contest_date(), "entries": leaderboard(db, contest_date())}

@router.get("/winner/latest")
def latest_winner(db: Session = Depends(get_db), token=Depends(get_optional_user_from_header)):
    user = user_from_token(token, db) if token else None
    yesterday = (now_ist().date().fromordinal(now_ist().date().toordinal() - 1)).isoformat()
    winner = decide_winner(db, yesterday)
    if not winner:
        return {"winner": None}
    attempt = db.query(RaceAttempt).filter_by(id=winner.attempt_id).first()
    result = {
        "contest_date": yesterday,
        "display_name": attempt.display_name if attempt else "Champion",
        "score": attempt.score if attempt else 0,
        "total_time_ms": attempt.total_time_ms if attempt else 0
    }
    if user and winner.user_id == user.id:
        result["real_name"] = user.name
        result["is_you"] = True
    else:
        result["is_you"] = False
    return {"winner": result}

@router.put("/display-name")
def display_name(payload: DisplayNameRequest, db: Session = Depends(get_db), token=Depends(get_current_user_from_header)):
    user = user_from_token(token, db)
    user.display_name = public_name(payload.display_name)
    db.commit()
    return {"display_name": user.display_name}

@router.get("/admin/leaderboard")
def admin_leaderboard(db: Session = Depends(get_db), token=Depends(get_current_user_from_header), request: Request = None):
    require_admin(token)
    if request:
        client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown").split(",")[0].strip()
        now = time.time()
        window_start = now - _ADMIN_RATE_WINDOW
        _ADMIN_RATE_LIMIT_STORE[client_ip] = [t for t in _ADMIN_RATE_LIMIT_STORE[client_ip] if t > window_start]
        if len(_ADMIN_RATE_LIMIT_STORE[client_ip]) >= _ADMIN_RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Too many admin requests. Please slow down and try again shortly.")
        _ADMIN_RATE_LIMIT_STORE[client_ip].append(now)
    attempts = db.query(RaceAttempt).filter_by(contest_date=contest_date(), status="completed").order_by(RaceAttempt.score.desc(), RaceAttempt.total_time_ms.asc(), RaceAttempt.completed_at.asc()).all()
    entries = []
    for rank, attempt in enumerate(attempts, start=1):
        user = db.query(UserProfile).filter_by(id=attempt.user_id).first()
        entries.append({
            "rank": rank,
            "display_name": attempt.display_name,
            "email": user.email if user else None,
            "score": attempt.score,
            "total_time_ms": attempt.total_time_ms,
            "finished_at": attempt.completed_at.isoformat() if attempt.completed_at else None
        })
    return {"contest_date": contest_date(), "entries": entries}

@router.get("/admin/day")
def admin_day(date_value: str | None = None, db: Session = Depends(get_db), token=Depends(get_current_user_from_header)):
    """Private daily audit: questions, submitted answers, ranking, and winner contact details."""
    require_admin(token)
    day = date_value or contest_date()
    quiz = db.query(RaceDailyQuiz).filter_by(contest_date=day).first()
    attempts = db.query(RaceAttempt).filter_by(contest_date=day, status="completed").order_by(
        RaceAttempt.score.desc(), RaceAttempt.total_time_ms.asc(), RaceAttempt.completed_at.asc()
    ).all()
    rows = []
    for rank, attempt in enumerate(attempts, start=1):
        user = db.query(UserProfile).filter_by(id=attempt.user_id).first()
        answers = db.query(RaceAnswer).filter_by(attempt_id=attempt.id).order_by(RaceAnswer.question_index).all()
        rows.append({
            "rank": rank,
            "display_name": attempt.display_name,
            "email": user.email if user else None,
            "score": attempt.score,
            "total_time_ms": attempt.total_time_ms,
            "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None,
            "answers": [
                {
                    "question_index": answer.question_index,
                    "selected_index": answer.selected_index,
                    "is_correct": bool(answer.is_correct),
                    "elapsed_ms": answer.elapsed_ms
                }
                for answer in answers
            ]
        })

    questions_list = []
    if quiz and quiz.questions_json:
        try:
            questions_list = json.loads(quiz.questions_json)
        except Exception:
            questions_list = []

    total_started = db.query(RaceAttempt).filter_by(contest_date=day).count()
    return {
        "contest_date": day,
        "theme": quiz.theme if quiz else "General AI & Career Competencies",
        "questions": questions_list,
        "top_three": rows[:3],
        "attempts": rows,
        "total_started": total_started,
        "total_completed": len(rows),
        "is_today": day == contest_date()
    }

@router.get("/admin/winners")
def admin_winners(db: Session = Depends(get_db), token=Depends(get_current_user_from_header)):
    require_admin(token)
    today = contest_date()
    # Backfill any past dates where winners have not been finalized yet
    past_dates = (
        db.query(RaceAttempt.contest_date)
        .filter(RaceAttempt.contest_date < today, RaceAttempt.status == "completed")
        .distinct()
        .all()
    )
    for (p_date,) in past_dates:
        decide_winner(db, p_date)

    # Only show winners from the past 30 days
    cutoff_date = (now_ist() - timedelta(days=30)).date().isoformat()
    winners = db.query(RaceWinner).filter(RaceWinner.contest_date >= cutoff_date).order_by(RaceWinner.contest_date.desc()).all()
    result = []
    for w in winners:
        user = db.query(UserProfile).filter_by(id=w.user_id).first()
        attempt = db.query(RaceAttempt).filter_by(id=w.attempt_id).first()
        result.append({
            "contest_date": w.contest_date,
            "attempt_id": w.attempt_id,
            "name": (user.name if user and user.name else None) or (attempt.display_name if attempt else "Candidate"),
            "email": (user.email if user and user.email else None) or "—",
            "score": attempt.score if attempt else 0,
            "total_time_ms": attempt.total_time_ms if attempt else 0,
            "completed_at": attempt.completed_at.isoformat() if attempt and attempt.completed_at else None
        })
    return result


@router.get("/admin/leaderboard/csv")
def admin_leaderboard_csv(date_value: str | None = None, db: Session = Depends(get_db), token=Depends(get_current_user_from_header)):
    """Download the daily leaderboard as a CSV before 7-day retention deletes it."""
    require_admin(token)
    day = date_value or contest_date()
    attempts = db.query(RaceAttempt).filter_by(contest_date=day, status="completed").order_by(
        RaceAttempt.score.desc(), RaceAttempt.total_time_ms.asc(), RaceAttempt.completed_at.asc()
    ).all()

    import io
    import csv
    from fastapi.responses import Response

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Rank", "Contest Date", "Display Name", "User Email", "Score", "Total Time Seconds", "Completed At"])
    for rank, attempt in enumerate(attempts, start=1):
        user = db.query(UserProfile).filter_by(id=attempt.user_id).first()
        writer.writerow([
            rank,
            attempt.contest_date,
            attempt.display_name,
            user.email if user else "",
            attempt.score,
            f"{attempt.total_time_ms / 1000.0:.2f}",
            attempt.completed_at.isoformat() if attempt.completed_at else ""
        ])

    csv_data = output.getvalue()
    filename = f"ai_race_leaderboard_{day}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
