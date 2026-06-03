# A.I.M. SQLite Bridge (`a3m_db_core`) - The "Golden" Binary

**⚠️ CRITICAL WARNING FOR A.I.M. AGENTS AND DEVELOPERS ⚠️**
This extension is explicitly tuned for the Arma 3 engine. **DO NOT** use standard JSON formatting libraries (like `serde_json`) to generate return strings. Arma 3's high-speed parser (`parseSimpleArray`) will fatally crash if you send it standard web JSON.

## The Architecture

Built in **Rust** using `arma-rs`, this extension provides a direct, memory-safe bridge to a local SQLite database, replacing unstable legacy C++ wrappers like `extDB3`.

### The `parseSimpleArray` Constraint (Why we don't use standard JSON)
To maximize SQF performance and avoid the `call compile` Remote Code Execution (RCE) vulnerability, the Arma mission exclusively uses `parseSimpleArray` to deserialize database strings.

1. **Double Quotes (`""`):** Standard JSON escapes internal quotes with a backslash (`\""). Arma 3 **cannot** read backslashes. It expects internal quotes to be escaped with a second quote (`""`).
2. **Boolean Strictness:** The Rust extension MUST return `1` (integer) for success, not `true` (boolean). Arma 3's SQF `isEqualTo` type-checking will silently fail if it receives a boolean when expecting a number.

*The source code in `rust_extension/src/lib.rs` explicitly replaces all `\"` with `""` natively before handing the string back to Arma. Do not "fix" this manual formatting.*

## SQF API Usage

The extension exposes four functions: `set`, `get`, `exec`, and a secure trigger `compile_leaderboard`.

### 1. Saving Data (Key-Value)
Quickly save or overwrite a string to a unique Key ID.
```sqf
_saveResult = "a3m_db_core" callExtension ["set", ["Player_765611980_Loadout", "['arifle_MX_F', 5000]"]];
// Returns: [1, "Saved"] (or [0, "error string"])
```

### 2. Loading Data (Key-Value)
Retrieve data by its exact Key ID.
```sqf
_loadResult = "a3m_db_core" callExtension ["get", ["Player_765611980_Loadout"]];
// Returns: [1, "['arifle_MX_F', 5000]"]
```

### 3. Secure Python Trigger
Executes a hardcoded system call to update the leaderboard, immune to RCE injection.
```sqf
_result = "a3m_db_core" callExtension ["compile_leaderboard"];
```

### 4. Executing Raw SQL
```sqf
_sqlResult = "a3m_db_core" callExtension ["exec", ["CREATE TABLE IF NOT EXISTS economy (faction TEXT, funds INTEGER)"]];
```

## Installation & Compiling (The Golden Build)

1. Navigate to the `rust_extension` directory.
2. Run: `cargo build --release`
3. The new compiled library will be output to: `target/release/liba3m_db_core.so`.
4. Copy it to your server mod folder and rename it: `cp target/release/liba3m_db_core.so /home/brian-vasquez/arma3server/@a3m_db_core/a3m_db_core_x64.so`
5. Add `-serverMod=@a3m_db_core` to your launch parameters.
6. The database generates automatically at: `a3m_database.sqlite` (in the server root). Alternatively, you can use the pre-packaged `example_a3m_database.sqlite` provided in this repository as a clean template.