# Masters Tournament Backend API - With JSON Import
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
import json
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

# Serve static files (add this import at the top if not already there)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

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
    
    # Check if we should load from JSON or use default data
    cursor.execute('SELECT COUNT(*) FROM tournaments')
    if cursor.fetchone()[0] == 0:
        if os.path.exists('masters_data.json'):
            print("Loading data from masters_data.json...")
            load_from_json(cursor)
        else:
            print("Loading default data...")
            insert_initial_data(cursor)
    
    conn.commit()
    conn.close()

def load_from_json(cursor):
    """Load tournament and golfer data from JSON file"""
    try:
        with open('masters_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Insert tournaments
        tournaments = data.get('tournaments', [])
        for tournament in tournaments:
            cursor.execute('''
                INSERT OR REPLACE INTO tournaments (year, winner, score, to_par, nationality)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                tournament['year'],
                tournament['winner'],
                tournament['score'],
                tournament['to_par'],
                tournament['nationality']
            ))
        
        # Insert golfers
        golfers = data.get('golfers', [])
        for golfer in golfers:
            cursor.execute('''
                INSERT OR REPLACE INTO golfers (name, bio, total_majors, turned_pro, nationality)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                golfer['name'],
                golfer.get('bio'),
                golfer.get('total_majors', 0),
                golfer.get('turned_pro'),
                golfer.get('nationality')
            ))
        
        print(f"Loaded {len(tournaments)} tournaments and {len(golfers)} golfers from JSON")
        
    except Exception as e:
        print(f"Error loading from JSON: {e}")
        print("Falling back to default data...")
        insert_initial_data(cursor)

def insert_initial_data(cursor):
    # Fallback data if JSON not available
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
        (2015, "Jordan Spieth", 270, -18, "USA")
    ]
    
    cursor.executemany(
        'INSERT INTO tournaments (year, winner, score, to_par, nationality) VALUES (?, ?, ?, ?, ?)',
        tournaments
    )
    
    golfers = [
        ("Tiger Woods", "Tiger Woods is one of the greatest golfers of all time, with 15 major championships including 5 Masters titles.", 15, 1996, "USA"),
        ("Scottie Scheffler", "Scottie Scheffler has emerged as one of golf's brightest stars, becoming the world's #1 ranked player.", 2, 2018, "USA")
    ]
    
    cursor.executemany(
        'INSERT INTO golfers (name, bio, total_majors, turned_pro, nationality) VALUES (?, ?, ?, ?, ?)',
        golfers
    )

# Pydantic models (keep all existing models)
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

# Authentication functions (keep existing)
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
    # If index.html exists, serve it; otherwise return API info
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    elif os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    else:
        return {
            "message": "Masters Tournament API", 
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health"
        }

# Admin endpoint to reload data from JSON
@app.post("/admin/reload-data")
async def reload_data_from_json(admin: str = Depends(verify_admin)):
    """Reload all data from masters_data.json file (admin only)"""
    if not os.path.exists('masters_data.json'):
        raise HTTPException(status_code=404, detail="masters_data.json file not found")
    
    try:
        conn = sqlite3.connect('masters.db')
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute('DELETE FROM tournaments')
        cursor.execute('DELETE FROM golfers')
        
        # Load from JSON
        load_from_json(cursor)
        
        conn.commit()
        conn.close()
        
        # Log admin action
        log_admin_action("RELOAD_DATA", "Reloaded all data from masters_data.json")
        
        return {"message": "Data successfully reloaded from masters_data.json"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reloading data: {str(e)}")

# Export current data to JSON
@app.get("/admin/export-data")
async def export_data_to_json(admin: str = Depends(verify_admin)):
    """Export current database data to JSON format (admin only)"""
    conn = sqlite3.connect('masters.db')
    cursor = conn.cursor()
    
    # Get all tournaments
    cursor.execute('SELECT year, winner, score, to_par, nationality FROM tournaments ORDER BY year DESC')
    tournament_rows = cursor.fetchall()
    
    tournaments = []
    for row in tournament_rows:
        tournaments.append({
            "year": row[0],
            "winner": row[1],
            "score": row[2],
            "to_par": row[3],
            "nationality": row[4]
        })
    
    # Get all golfers
    cursor.execute('SELECT name, bio, total_majors, turned_pro, nationality FROM golfers ORDER BY name')
    golfer_rows = cursor.fetchall()
    
    golfers = []
    for row in golfer_rows:
        golfers.append({
            "name": row[0],
            "bio": row[1],
            "total_majors": row[2],
            "turned_pro": row[3],
            "nationality": row[4]
        })
    
    conn.close()
    
    export_data = {
        "tournaments": tournaments,
        "golfers": golfers
    }
    
    # Log admin action
    log_admin_action("EXPORT_DATA", f"Exported {len(tournaments)} tournaments and {len(golfers)} golfers")
    
    return export_data

# Keep all existing API endpoints (tournaments, golfers, search, stats, admin endpoints)
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