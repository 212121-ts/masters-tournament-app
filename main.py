# Masters Tournament Backend API - Production Version
# Run with: uvicorn main:app --host 0.0.0.0 --port $PORT

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import hashlib
import secrets
import os
from datetime import datetime

app = FastAPI(title="Masters Tournament API", version="1.0.0")

# Environment variables for production
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "masters2024!")
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if FRONTEND_URL == "*" else [FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBasic()

# Admin credentials (using environment variables)
ADMIN_PASSWORD_HASH = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()

# Database setup
def init_database():
    conn = sqlite3.connect('masters.db')
    cursor = conn.cursor()
    
    # Create tournaments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER UNIQUE NOT NULL,
            winner TEXT NOT NULL,
            score INTEGER NOT NULL,
            to_par INTEGER NOT NULL,
            nationality TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create golfers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS golfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            bio TEXT,
            total_majors INTEGER DEFAULT 0,
            turned_pro INTEGER,
            nationality TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create admin_logs table for tracking changes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert initial data if tables are empty
    cursor.execute('SELECT COUNT(*) FROM tournaments')
    if cursor.fetchone()[0] == 0:
        insert_initial_data(cursor)
    
    conn.commit()
    conn.close()

def insert_initial_data(cursor):
    # Initial tournament data
    tournaments = [
        (2024, "Scottie Scheffler", 277, -11, "USA"),
        (2023, "Jon Rahm", 276, -12, "ESP"),
        (2022, "Scottie Scheffler", 278, -10, "USA"),
        (2021, "Hideki Matsuyama", 278, -10, "JPN"),
        (2020, "Dustin Johnson", 268, -20, "USA"),
        (2019, "Tiger Woods", 275, -13, "USA"),
        (2018, "Patrick Reed", 273, -15, "USA"),
        (2017, "Sergio García", 279, -9, "ESP"),
        (2016, "Danny Willett", 283, -5, "ENG"),
        (2015, "Jordan Spieth", 270, -18, "USA"),
        (2014, "Bubba Watson", 280, -8, "USA"),
        (2013, "Adam Scott", 279, -9, "AUS"),
        (2012, "Bubba Watson", 278, -10, "USA"),
        (2011, "Charl Schwartzel", 274, -14, "RSA"),
        (2010, "Phil Mickelson", 272, -16, "USA"),
        (2009, "Ángel Cabrera", 276, -12, "ARG"),
        (2008, "Trevor Immelman", 280, -8, "RSA"),
        (2007, "Zach Johnson", 289, 1, "USA"),
        (2006, "Phil Mickelson", 281, -7, "USA"),
        (2005, "Tiger Woods", 276, -12, "USA"),
        (2004, "Phil Mickelson", 279, -9, "USA"),
        (2003, "Mike Weir", 281, -7, "CAN"),
        (2002, "Tiger Woods", 276, -12, "USA"),
        (2001, "Tiger Woods", 272, -16, "USA"),
        (2000, "Vijay Singh", 278, -10, "FJI"),
        (1999, "José María Olazábal", 280, -8, "ESP"),
        (1998, "Mark O'Meara", 279, -9, "USA"),
        (1997, "Tiger Woods", 270, -18, "USA"),
        (1996, "Nick Faldo", 276, -12, "ENG"),
        (1995, "Ben Crenshaw", 274, -14, "USA")
    ]
    
    cursor.executemany(
        'INSERT INTO tournaments (year, winner, score, to_par, nationality) VALUES (?, ?, ?, ?, ?)',
        tournaments
    )
    
    # Initial golfer bios
    golfers = [
        ("Tiger Woods", "Tiger Woods is one of the greatest golfers of all time, with 15 major championships including 5 Masters titles. His 1997 Masters victory at age 21 was historic, winning by 12 strokes with a record-breaking score of 270. Known for his incredible comeback story, including his 2019 Masters victory after personal and physical struggles.", 15, 1996, "USA"),
        ("Phil Mickelson", "Phil Mickelson, known as 'Lefty', is a fan favorite with 6 major championships including 3 Masters titles. Known for his aggressive play style and short game wizardry, he's one of the most popular players in golf history. His left-handed swing and charismatic personality have made him a household name.", 6, 1992, "USA"),
        ("Scottie Scheffler", "Scottie Scheffler has emerged as one of golf's brightest stars, becoming the world's #1 ranked player. His consistent play and mental toughness have led to multiple PGA Tour victories including back-to-back Masters wins in 2022 and 2024. Known for his steady demeanor and excellent ball-striking.", 2, 2018, "USA"),
        ("Bubba Watson", "Bubba Watson is known for his incredible length off the tee and creative shot-making ability. His two Masters victories showcase his unique style and ability to shape shots around Augusta National's challenging layout. Watson's emotional celebrations and colorful personality have made him a fan favorite.", 2, 2003, "USA"),
        ("Jordan Spieth", "Jordan Spieth burst onto the scene with his dominant 2015 Masters victory, tying Tiger Woods' scoring record of 270. Known for his exceptional putting and course management, Spieth won three majors before age 24. His Masters win was part of an incredible year that included the U.S. Open.", 3, 2012, "USA")
    ]
    
    cursor.executemany(
        'INSERT INTO golfers (name, bio, total_majors, turned_pro, nationality) VALUES (?, ?, ?, ?, ?)',
        golfers
    )

# Pydantic models
class Tournament(BaseModel):
    year: int
    winner: str
    score: int
    to_par: int
    nationality: str

class TournamentResponse(Tournament):
    id: int
    created_at: str
    updated_at: str

class Golfer(BaseModel):
    name: str
    bio: Optional[str] = None
    total_majors: Optional[int] = 0
    turned_pro: Optional[int] = None
    nationality: Optional[str] = None

class GolferResponse(Golfer):
    id: int
    masters_wins: List[int]
    created_at: str
    updated_at: str

# Authentication
def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    is_correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    is_correct_password = secrets.compare_digest(
        hashlib.sha256(credentials.password.encode()).hexdigest(),
        ADMIN_PASSWORD_HASH
    )
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def log_admin_action(action: str, details: str):
    conn = sqlite3.connect('masters.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO admin_logs (action, details) VALUES (?, ?)',
        (action, details)
    )
    conn.commit()
    conn.close()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Masters Tournament API"}

@app.get("/")
async def root():
    return {
        "message": "Masters Tournament API", 
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/tournaments", response_model=List[TournamentResponse])
async def get_all_tournaments():
    """Get all tournament results"""
    conn = sqlite3.connect('masters.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tournaments ORDER BY year DESC')
    rows = cursor.fetchall()
    conn.close()
    
    tournaments = []
    for row in rows:
        tournaments.append({
            "id": row[0],
            "year": row[1],
            "winner": row[2],
            "score": row[3],
            "to_par": row[4],
            "nationality": row[5],
            "created_at": row[6],
            "updated_at": row[7]
        })
    
    return tournaments

@app.get("/tournaments/{year}", response_model=TournamentResponse)
async def get_tournament_by_year(year: int):
    """Get tournament result by year"""
    conn = sqlite3.connect('masters.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tournaments WHERE year = ?', (year,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    return {
        "id": row[0],
        "year": row[1],
        "winner": row[2],
        "score": row[3],
        "to_par": row[4],
        "nationality": row[5],
        "created_at": row[6],
        "updated_at": row[7]
    }

@app.get("/golfers", response_model=List[GolferResponse])
async def get_all_golfers():
    """Get all golfers with their Masters wins"""
    conn = sqlite3.connect('masters.db')
    cursor = conn.cursor()
    
    # Get all golfers
    cursor.execute('SELECT * FROM golfers ORDER BY name')
    golfer_rows = cursor.fetchall()
    
    golfers = []
    for row in golfer_rows:
        # Get Masters wins for this golfer
        cursor.execute('SELECT year FROM tournaments WHERE winner = ? ORDER BY year DESC', (row[1],))
        wins = [win[0] for win in cursor.fetchall()]
        
        golfers.append({
            "id": row[0],
            "name": row[1],
            "bio": row[2],
            "total_majors": row[3],
            "turned_pro": row[4],
            "nationality": row[5],
            "masters_wins": wins,
            "created_at": row[6],
            "updated_at": row[7]
        })
    
    conn.close()
    return golfers

@app.get("/golfers/{golfer_name}", response_model=GolferResponse)
async def get_golfer_by_name(golfer_name: str):
    """Get golfer details and Masters wins"""
    conn = sqlite3.connect('masters.db')
    cursor = conn.cursor()
    
    # Get golfer info
    cursor.execute('SELECT * FROM golfers WHERE name = ?', (golfer_name,))
    row = cursor.fetchone()
    
    if not row:
        # If golfer not in golfers table, check if they're in tournaments
        cursor.execute('SELECT DISTINCT winner FROM tournaments WHERE winner = ?', (golfer_name,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Golfer not found")
        
        # Create basic golfer entry
        row = (None, golfer_name, None, 0, None, None, None, None)
    
    # Get Masters wins
    cursor.execute('SELECT year FROM tournaments WHERE winner = ? ORDER BY year DESC', (golfer_name,))
    wins = [win[0] for win in cursor.fetchall()]
    
    conn.close()
    
    return {
        "id": row[0] or 0,
        "name": row[1],
        "bio": row[2],
        "total_majors": row[3] or len(wins),
        "turned_pro": row[4],
        "nationality": row[5],
        "masters_wins": wins,
        "created_at": row[6] or "",
        "updated_at": row[7] or ""
    }

@app.get("/search")
async def search_tournaments(q: str):
    """Search tournaments by year or golfer name"""
    conn = sqlite3.connect('masters.db')
    cursor = conn.cursor()
    
    # Try to parse as year
    try:
        year = int(q)
        cursor.execute('SELECT * FROM tournaments WHERE year = ?', (year,))
        rows = cursor.fetchall()
    except ValueError:
        # Search by golfer name
        cursor.execute('SELECT * FROM tournaments WHERE winner LIKE ? ORDER BY year DESC', (f'%{q}%',))
        rows = cursor.fetchall()
    
    conn.close()
    
    tournaments = []
    for row in rows:
        tournaments.append({
            "id": row[0],
            "year": row[1],
            "winner": row[2],
            "score": row[3],
            "to_par": row[4],
            "nationality": row[5],
            "created_at": row[6],
            "updated_at": row[7]
        })
    
    return tournaments

@app.get("/stats")
async def get_tournament_stats():
    """Get tournament statistics"""
    conn = sqlite3.connect('masters.db')
    cursor = conn.cursor()
    
    # Total years
    cursor.execute('SELECT COUNT(*) FROM tournaments')
    total_years = cursor.fetchone()[0]
    
    # Unique winners
    cursor.execute('SELECT COUNT(DISTINCT winner) FROM tournaments')
    unique_winners = cursor.fetchone()[0]
    
    # Best score
    cursor.execute('SELECT MIN(score) FROM tournaments')
    best_score = cursor.fetchone()[0]
    
    # Most wins by a golfer
    cursor.execute('SELECT winner, COUNT(*) as wins FROM tournaments GROUP BY winner ORDER BY wins DESC LIMIT 1')
    most_wins_data = cursor.fetchone()
    most_wins = most_wins_data[1] if most_wins_data else 0
    most_wins_golfer = most_wins_data[0] if most_wins_data else ""
    
    conn.close()
    
    return {
        "total_years": total_years,
        "unique_winners": unique_winners,
        "best_score": best_score,
        "most_wins": most_wins,
        "most_wins_golfer": most_wins_golfer
    }

# Admin endpoints (require authentication)

@app.post("/admin/tournaments", response_model=TournamentResponse)
async def add_tournament(tournament: Tournament, admin: str = Depends(verify_admin)):
    """Add or update tournament result (admin only)"""
    conn = sqlite3.connect('masters.db')
    cursor = conn.cursor()
    
    # Check if year already exists
    cursor.execute('SELECT id FROM tournaments WHERE year = ?', (tournament.year,))
    existing = cursor.fetchone()
    
    if existing:
        # Update existing tournament
        cursor.execute('''
            UPDATE tournaments 
            SET winner = ?, score = ?, to_par = ?, nationality = ?, updated_at = CURRENT_TIMESTAMP
            WHERE year = ?
        ''', (tournament.winner, tournament.score, tournament.to_par, tournament.nationality, tournament.year))
        action = "UPDATE"
    else:
        # Insert new tournament
        cursor.execute('''
            INSERT INTO tournaments (year, winner, score, to_par, nationality)
            VALUES (?, ?, ?, ?, ?)
        ''', (tournament.year, tournament.winner, tournament.score, tournament.to_par, tournament.nationality))
        action = "INSERT"
    
    # Get the updated/inserted record
    cursor.execute('SELECT * FROM tournaments WHERE year = ?', (tournament.year,))
    row = cursor.fetchone()
    
    conn.commit()
    conn.close()
    
    # Log admin action
    log_admin_action(
        action,
        f"Tournament {tournament.year}: {tournament.winner} ({tournament.score}, {tournament.to_par})"
    )
    
    return {
        "id": row[0],
        "year": row[1],
        "winner": row[2],
        "score": row[3],
        "to_par": row[4],
        "nationality": row[5],
        "created_at": row[6],
        "updated_at": row[7]
    }

@app.post("/admin/golfers", response_model=GolferResponse)
async def add_or_update_golfer(golfer: Golfer, admin: str = Depends(verify_admin)):
    """Add or update golfer bio (admin only)"""
    conn = sqlite3.connect('masters.db')
    cursor = conn.cursor()
    
    # Check if golfer already exists
    cursor.execute('SELECT id FROM golfers WHERE name = ?', (golfer.name,))
    existing = cursor.fetchone()
    
    if existing:
        # Update existing golfer
        cursor.execute('''
            UPDATE golfers 
            SET bio = ?, total_majors = ?, turned_pro = ?, nationality = ?, updated_at = CURRENT_TIMESTAMP
            WHERE name = ?
        ''', (golfer.bio, golfer.total_majors, golfer.turned_pro, golfer.nationality, golfer.name))
        action = "UPDATE"
    else:
        # Insert new golfer
        cursor.execute('''
            INSERT INTO golfers (name, bio, total_majors, turned_pro, nationality)
            VALUES (?, ?, ?, ?, ?)
        ''', (golfer.name, golfer.bio, golfer.total_majors, golfer.turned_pro, golfer.nationality))
        action = "INSERT"
    
    # Get Masters wins
    cursor.execute('SELECT year FROM tournaments WHERE winner = ? ORDER BY year DESC', (golfer.name,))
    wins = [win[0] for win in cursor.fetchall()]
    
    # Get the updated/inserted record
    cursor.execute('SELECT * FROM golfers WHERE name = ?', (golfer.name,))
    row = cursor.fetchone()
    
    conn.commit()
    conn.close()
    
    # Log admin action
    log_admin_action(action, f"Golfer: {golfer.name}")
    
    return {
        "id": row[0],
        "name": row[1],
        "bio": row[2],
        "total_majors": row[3],
        "turned_pro": row[4],
        "nationality": row[5],
        "masters_wins": wins,
        "created_at": row[6],
        "updated_at": row[7]
    }

@app.delete("/admin/tournaments/{year}")
async def delete_tournament(year: int, admin: str = Depends(verify_admin)):
    """Delete tournament by year (admin only)"""
    conn = sqlite3.connect('masters.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT winner FROM tournaments WHERE year = ?', (year,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    winner = result[0]
    cursor.execute('DELETE FROM tournaments WHERE year = ?', (year,))
    conn.commit()
    conn.close()
    
    # Log admin action
    log_admin_action("DELETE", f"Tournament {year}: {winner}")
    
    return {"message": f"Tournament {year} deleted successfully"}

@app.get("/admin/logs")
async def get_admin_logs(admin: str = Depends(verify_admin)):
    """Get admin action logs (admin only)"""
    conn = sqlite3.connect('masters.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM admin_logs ORDER BY timestamp DESC LIMIT 100')
    rows = cursor.fetchall()
    conn.close()
    
    logs = []
    for row in rows:
        logs.append({
            "id": row[0],
            "action": row[1],
            "details": row[2],
            "timestamp": row[3]
        })
    
    return logs

# Initialize database on startup
init_database()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)