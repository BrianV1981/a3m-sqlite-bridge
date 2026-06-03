// a3m_db_core Usage Examples

// 1. Initializing and testing the connection on Server Boot
// (Place this inside initServer.sqf)
diag_log "Initializing a3m_db_core SQLite Bridge...";
_saveResult = "a3m_db_core" callExtension ["set", ["Server_Boot_Test", "Online"]];
diag_log format ["[DB_TEST] Write Result: %1", _saveResult];

_loadResult = "a3m_db_core" callExtension ["get", ["Server_Boot_Test"]];
diag_log format ["[DB_TEST] Read Result: %1", _loadResult];


// 2. Saving a player's loadout (HashMap/Array) to the database
A3M_fnc_savePlayerData = {
    params ["_playerUID", "_playerDataArray"];
    
    // Convert the array/hashmap to a string before saving
    private _dataString = str _playerDataArray;
    private _key = format ["Player_%1_Data", _playerUID];
    
    private _result = "a3m_db_core" callExtension ["set", [_key, _dataString]];
    
    // Check if it saved successfully
    private _parsedResult = parseSimpleArray _result;
    if (_parsedResult select 0) then {
        diag_log format ["Successfully saved data for %1", _playerUID];
    } else {
        diag_log format ["ERROR: Failed to save data for %1. Reason: %2", _playerUID, _parsedResult select 1];
    };
};


// 3. Loading a player's loadout from the database
A3M_fnc_loadPlayerData = {
    params ["_playerUID"];
    
    private _key = format ["Player_%1_Data", _playerUID];
    private _result = "a3m_db_core" callExtension ["get", [_key]];
    
    private _parsedResult = parseSimpleArray _result;
    private _playerDataArray = [];
    
    if (_parsedResult select 0) then {
        private _dataString = _parsedResult select 1;
        if (_dataString != "") then {
            // Convert the string back into an SQF Array/HashMap
            _playerDataArray = parseSimpleArray _dataString;
            diag_log format ["Successfully loaded data for %1", _playerUID];
        } else {
            diag_log format ["No existing data found for %1. Creating new profile.", _playerUID];
        };
    } else {
        diag_log format ["ERROR: Failed to load data for %1. Reason: %2", _playerUID, _parsedResult select 1];
    };
    
    _playerDataArray
};
