# A.I.M. Database Performance & Anti-Bottleneck Architecture

## 1. The Threat: Thread Locking
The `a3m_db_core` Rust extension interfaces with an embedded SQLite database. While SQLite is capable of >100,000 operations per second, the bottleneck lies within the **Arma 3 Engine Scheduler**.

When SQF executes `"a3m_db_core" callExtension ["set", ...]`, Arma 3 physically halts the main execution thread until the extension returns a value. 
*   **The Risk:** If multiple heavy systems (HG Garages, Grad-Persistence, AI Virtual Barracks, ALiVE) attempt to write thousands of entries simultaneously, the server will experience severe FPS drops (micro-stuttering) or even network desync as the engine waits for sequential disk I/O.

## 2. Core Mitigation Strategies

To ensure the server remains at 50+ FPS regardless of database load, all persistent systems MUST adhere to the following three architectural rules:

### A. Volatile Memory Buffering (No Live Writes)
**Rule:** Never execute a database `set` call during live combat or rapid events.
*   **Implementation:** When a player earns money, places a sandbag, or scores a kill, update an array or HashMap stored in the server's RAM (volatile memory). 
*   **Execution:** Only commit this RAM buffer to the SQLite database during designated low-impact events:
    1. `onPlayerDisconnected`
    2. Scheduled Auto-Save Intervals
    3. Server Shutdown sequences

### B. Data Chunking (JSON Blobs)
**Rule:** Minimize the number of `callExtension` executions by packing data.
*   100 `callExtension` calls to save 100 vehicles = **Fatal**.
*   1 `callExtension` call containing a serialized array of 100 vehicles = **Optimal**.
*   **Implementation:** Rely on `grad-persistence` and our custom wrappers to serialize massive arrays into single strings. SQLite `TEXT` columns can hold up to 1GB of string data per cell. Let Rust and SQLite handle the massive string parse; keep the Arma 3 call count to an absolute minimum.

### C. The Staggered Auto-Save Queue
**Rule:** Never execute a mass server auto-save in a single, unscheduled frame.
*   **Implementation:** When writing auto-save loops for the server, you MUST use `spawn` and `sleep` to yield execution time back to the main Arma 3 engine.

**Example of the Staggered Save Loop:**
```sqf
A3M_fnc_serverAutoSave = {
    [] spawn {
        diag_log "[A3M Auto-Save] Initiating staggered save sequence...";

        // 1. Save Players (Staggered by 0.5 seconds per player)
        {
            private _playerData = [_x] call A3M_fnc_compilePlayerStats;
            [format["Player_%1", getPlayerUID _x], _playerData] call A3M_fnc_dbSet;
            sleep 0.5; // Yield to engine physics/network
        } forEach allPlayers;

        // 2. Heavy Pause between systems
        sleep 5; 

        // 3. Save Virtual Barracks (One massive chunk)
        private _barracksData = call A3M_fnc_compileBarracks;
        ["Global_Virtual_Barracks", _barracksData] call A3M_fnc_dbSet;

        // 4. Heavy Pause
        sleep 5;

        // 5. Trigger Grad-Persistence Save
        [] call grad_persistence_fnc_saveMission;
        
        diag_log "[A3M Auto-Save] Sequence Complete.";
    };
};
```

## 3. System-Specific Guidelines

*   **HG Garages:** Safe to save immediately upon the player clicking "Store Vehicle" in the UI, as this is a singular, low-frequency event.
*   **Grad-Fortifications:** Do not save on placement. Rely on the staggered auto-save loop to chunk the entire map's fortifications at once.
*   **Scoreboard / Economy:** Update HashMaps via `EntityKilled` event handlers. Only commit to SQLite on disconnect or during the staggered auto-save.
