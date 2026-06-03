use arma_rs::{arma, Extension};
use rusqlite::Connection;
use std::process::Command;

fn get_conn() -> Result<Connection, String> {
    let conn = Connection::open("/home/brian-vasquez/arma3server/a3m_database.sqlite")
        .map_err(|e| e.to_string())?;
    
    conn.execute(
        "CREATE TABLE IF NOT EXISTS store (
            id TEXT PRIMARY KEY,
            val TEXT NOT NULL
        )",
        [],
    ).map_err(|e| e.to_string())?;
    
    Ok(conn)
}

#[arma]
fn init() -> Extension {
    Extension::build()
        .command("get", get)
        .command("set", set)
        .command("exec", execute)
        .command("compile_leaderboard", compile_leaderboard)
        .finish()
}

fn set(key: String, value: String) -> String {
    let conn = match get_conn() {
        Ok(c) => c,
        Err(e) => return format!("[0, \"{}\"]", e.replace("\"", "\"\"")),
    };
    
    match conn.execute("INSERT OR REPLACE INTO store (id, val) VALUES (?1, ?2)", [&key, &value]) {
        Ok(_) => "[1, \"Saved\"]".to_string(),
        Err(e) => format!("[0, \"{}\"]", e.to_string().replace("\"", "\"\"")),
    }
}

fn get(key: String) -> String {
    let conn = match get_conn() {
        Ok(c) => c,
        Err(e) => return format!("[0, \"{}\"]", e.replace("\"", "\"\"")),
    };
    
    let mut stmt = match conn.prepare("SELECT val FROM store WHERE id = ?1") {
        Ok(s) => s,
        Err(e) => return format!("[0, \"{}\"]", e.to_string().replace("\"", "\"\"")),
    };
    
    let mut rows = match stmt.query([&key]) {
        Ok(r) => r,
        Err(e) => return format!("[0, \"{}\"]", e.to_string().replace("\"", "\"\"")),
    };
    
    if let Ok(Some(row)) = rows.next() {
        let val: String = row.get(0).unwrap_or_default();
        // The Golden Fix: Replace all standard quotes with Arma-native double quotes
        format!("[1, \"{}\"]", val.replace("\"", "\"\""))
    } else {
        "[1, \"\"]".to_string() // Return empty string if not found
    }
}

fn execute(sql: String) -> String {
    let conn = match get_conn() {
        Ok(c) => c,
        Err(e) => return format!("[0, \"{}\"]", e.replace("\"", "\"\"")),
    };
    match conn.execute(&sql, []) {
         Ok(rows) => format!("[1, {}]", rows),
         Err(e) => format!("[0, \"{}\"]", e.to_string().replace("\"", "\"\"")),
    }
}

fn compile_leaderboard() -> String {
    let status = Command::new("/usr/bin/python3")
        .arg("/home/brian-vasquez/aim-arma/scripts/compile_global_leaderboards.py")
        .status();

    match status {
        Ok(s) if s.success() => "[1, \"Compiled successfully\"]".to_string(),
        Ok(s) => format!("[0, \"Script exited with status: {}\"]", s),
        Err(e) => format!("[0, \"Failed to execute script: {}\"]", e.to_string().replace("\"", "\"\"")),
    }
}