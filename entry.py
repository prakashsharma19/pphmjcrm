<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advertisements-PPH</title>
    <style>
        body {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            background-color: #f4f4f4;
            padding: 20px;
            margin: 0;
            color: #333;
            position: relative;
        }

        h1 {
            color: #1171ba;
            text-align: center;
            margin-bottom: 30px;
            font-size: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        h1 img {
            margin-right: 10px;
            height: 28px;
        }

        .font-controls,
        .login-container {
            background-color: #ffffff;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            width: 100%;
        }

        .font-controls .control-group {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            gap: 10px;
        }

        .font-controls label {
            margin-right: 10px;
            font-weight: bold;
            color: #2c3e50;
        }

        .font-controls select,
        .font-controls input {
            border-radius: 5px;
            padding: 5px;
            border: 1px solid #e0e0e0;
            font-size: 14px;
        }

        .font-controls input[type="number"] {
            width: 50px;
        }

        .fullscreen-button {
            background-color: #1171ba;
            border: none;
            color: white;
            padding: 10px 15px;
            font-size: 16px;
            cursor: pointer;
            border-radius: 5px;
            margin-top: 10px;
            width: 100%;
        }

        .fullscreen-button:hover {
            background-color: #0e619f;
        }

        .clear-memory-button {
            background-color: red;
            color: white;
            padding: 10px 15px;
            font-size: 16px;
            cursor: pointer;
            border-radius: 5px;
            border: none;
            position: absolute;
            top: 20px;
            left: 20px;
        }

        .clear-memory-button:hover {
            background-color: darkred;
        }

        .text-container {
            background-color: #ffffff;
            padding: 15px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            white-space: pre-wrap;
            position: relative;
            margin-top: 20px;
            z-index: 2;
            max-height: 500px;
            overflow-y: auto;
        }

        .text-container p {
            margin: 0 0 10px;
            border-bottom: 1px solid #e0e0e0;
            line-height: 1.5;
            transition: all 0.1s ease-out;
        }

        /* Toggle Switch Style */
        .switch {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 24px;
        }

        .switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: 0.4s;
            border-radius: 24px;
        }

        .slider:before {
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: 0.4s;
            border-radius: 50%;
        }

        input:checked + .slider {
            background-color: #1171ba;
        }

        input:checked + .slider:before {
            transform: translateX(26px);
        }

        .toggle-container {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }

        #dearProfessorLabel {
            font-size: 14px;
            color: #333;
        }

        #undoButton,
        #lockButton {
            border: none;
            color: white;
            padding: 10px 15px;
            font-size: 16px;
            cursor: pointer;
            border-radius: 5px;
            transition: background-color 0.3s, transform 0.1s ease;
            margin-top: 10px;
            width: 100%;
        }

        #loginButton {
            background-color: #007bff;
            margin-top: 10px;
            font-size: 16px;
            border: none;
            color: white;
            padding: 10px 15px;
            cursor: pointer;
            border-radius: 5px;
            transition: background-color 0.3s ease;
        }

        #loginButton:hover {
            background-color: #0056b3;
        }

        #loginButton:active {
            transform: scale(0.95);
        }

        #lockButton {
            background-color: #1171ba;
        }

        #lockButton.locked {
            background-color: #d9534f;
        }

        #lockButton:hover {
            background-color: #0e619f;
        }

        #undoButton {
            background-color: #1171ba;
        }

        .input-container {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
            flex-direction: column;
            align-items: center;
        }

        .input-container textarea {
            width: 100%;
            border-radius: 5px;
            padding: 10px;
            font-size: 16px;
            border: 1px solid #e0e0e0;
            margin-top: 10px;
        }

        .input-container .container-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            background-color: #1171ba;
            color: white;
            padding: 10px;
            border-radius: 5px;
        }

        .rough-container {
            width: 30%;
            margin-left: 0%;
        }

        .input-boxes {
            display: none;
        }

        #okButton {
            align-self: flex-end;
            background-color: #28a745;
            border: none;
            color: white;
            padding: 10px 20px;
            font-size: 14px;
            cursor: pointer;
            border-radius: 5px;
            margin-top: 10px;
        }

        #okButton:hover {
            background-color: #218838;
        }

        #adCount,
        #dailyAdCount,
        #remainingTime,
        #countryCount {
            margin-top: 15px;
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
        }

        #loadingIndicator {
            color: red;
            margin-left: 10px;
            font-size: 16px;
            font-weight: bold;
            display: none;
        }

        #remainingTime .hourglass {
            vertical-align: middle;
        }

        #countryCount {
            position: absolute;
            left: 20px;
            top: 250px;
            font-size: 16px;
            font-weight: bold;
            line-height: 1.5;
            color: #34495e;
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            max-height: 600px;
            overflow-y: auto;
            width: 300px;
            z-index: 100;
        }

        #cursorStart {
            font-weight: bold;
            color: #3498db;
        }

        #userControls {
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 16px;
            color: #34495e;
            display: flex;
            align-items: center;
        }

        #userControls img {
            margin-right: 10px;
            height: 28px;
        }

        #userControls span {
            margin-right: 10px;
            font-weight: bold;
        }

        #logoutButton {
            background-color: #e74c3c;
            border: none;
            color: white;
            padding: 5px 10px;
            font-size: 14px;
            cursor: pointer;
            border-radius: 5px;
        }

        #logoutButton:hover {
            background-color: #c0392b;
        }

        .error {
            color: #e74c3c;
            font-weight: bold;
            font-style: italic;
        }

        .highlight-added {
            background-color: #f4e542;
        }

        .login-container input {
            width: 100%;
            margin: 5px 0;
            padding: 10px;
            font-size: 16px;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
        }

        .hourglass {
            width: 24px;
            height: 24px;
            background-image: url('https://upload.wikimedia.org/wikipedia/commons/4/4e/Simpleicons_Interface_hourglass.svg');
            background-size: cover;
            display: inline-block;
            margin-left: 10px;
        }

        .top-controls {
            display: flex;
            justify-content: flex-start;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }

        .right-content {
            position: absolute;
            top: 250px;
            right: 20px;
            width: 150px;
        }

        #currentTime {
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            text-align: right;
        }

        #remainingTimeText {
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            text-align: right;
        }

        .reminder-heading {
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            text-align: right;
        }

        .reminder-slots {
            list-style-type: none;
            padding: 0;
            margin: 0;
            text-align: right;
        }

        .reminder-slots li {
            background-color: #d3eaf7;
            color: #333;
            padding: 5px;
            border-radius: 5px;
            margin-bottom: 5px;
            cursor: pointer;
            font-size: 12px;
            transition: background-color 0.3s;
        }

        .reminder-slots li:hover,
        .reminder-slots li.selected {
            background-color: #1171ba;
            color: white;
        }

        .popup {
            display: none;
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            padding: 30px;
            background-color: #2c3e50;
            color: white;
            border: 2px solid #e74c3c;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
            z-index: 1000;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
        }

        .popup button {
            background-color: #e74c3c;
            border: none;
            color: white;
            padding: 15px 30px;
            font-size: 18px;
            cursor: pointer;
            border-radius: 5px;
            transition: background-color 0.3s, transform 0.1s ease;
            margin-top: 20px;
        }

        .popup button:hover {
            background-color: #c0392b;
        }

        .popup button:active {
            transform: scale(0.95);
        }

        .popup img {
            width: 50px;
            height: 50px;
            margin-bottom: 20px;
        }

        .problem-heading {
            color: #e74c3c;
            font-style: italic;
            margin-top: 10px;
            font-size: 16px;
            font-weight: bold;
        }

        .reminder-note {
            font-style: italic;
            font-size: 12px;
            text-align: right;
            margin-top: 5px;
            color: #333;
        }

        /* Progress bar */
        .progress-bar-container {
            width: 100%;
            height: 5px;
            background-color: #e0e0e0;
            border-radius: 5px;
            margin-top: 20px;
            overflow: hidden;
        }

        .progress-bar {
            height: 100%;
            width: 0;
            background-color: #f00;
            transition: width 0.5s ease-in-out, background-color 0.5s ease-in-out;
        }

        .scroll-locked {
            overflow: hidden;
        }

        .scroll-lock-notice {
            position: fixed;
            bottom: 10px;
            left: 10px;
            background-color: #e74c3c;
            color: white;
            padding: 10px;
            border-radius: 5px;
            z-index: 10000;
            font-size: 14px;
            display: none;
        }

        /* Animations */
        @keyframes fadeOut {
            0% {
                opacity: 1;
            }
            100% {
                opacity: 0;
            }
        }

        @keyframes vanish {
            0% {
                transform: scale(1);
                opacity: 1;
            }
            100% {
                transform: scale(0);
                opacity: 0;
            }
        }

        @keyframes explode {
            0% {
                transform: scale(1);
                opacity: 1;
            }
            100% {
                transform: scale(3);
                opacity: 0;
            }
        }

        .fadeOut {
            animation: fadeOut 0.1s forwards;
        }

        .vanish {
            animation: vanish 0.1s forwards;
        }

        .explode {
            animation: explode 0.1s forwards;
        }

        .highlight-added {
            background-color: #f4e542;
        }

        /* Credit Section */
        #credit {
            position: fixed;
            bottom: 10px;
            right: 10px;
            font-size: 12px;
            color: #34495e;
        }

        #credit a {
            color: #1171ba;
            text-decoration: none;
        }

        #credit a:hover {
            text-decoration: underline;
        }

        /* Right Sidebar for Buttons */
        #rightSidebar {
            margin-top: 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            align-items: flex-end;
            z-index: 999;
        }

        /* Options in the font control pane */
        .gap-control {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            margin-top: 10px;
        }

        /* Country Filter Section */
        .country-filter {
            margin-top: 10px;
        }

        .country-item {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }

        .country-toggle {
            margin-right: 10px;
        }

        .country-name {
            flex-grow: 1;
        }

        .country-count {
            font-weight: bold;
            margin-left: 10px;
        }

        /* Group Management Section */
        .group-management {
            margin-top: 15px;
            border-top: 1px solid #e0e0e0;
            padding-top: 10px;
        }

        .group-item {
            margin-bottom: 10px;
            padding: 8px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }

        .group-toggle {
            margin-right: 10px;
        }

        .group-name {
            font-weight: bold;
            margin-bottom: 5px;
        }

        .group-countries {
            font-size: 12px;
            color: #666;
            margin-left: 20px;
            margin-bottom: 5px;
        }

        .group-controls {
            margin-top: 10px;
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }

        .group-input {
            width: 150px;
            padding: 5px;
            margin-right: 5px;
            border: 1px solid #e0e0e0;
            border-radius: 3px;
        }

        .group-button {
            padding: 5px 10px;
            background-color: #1171ba;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
        }

        .group-button:hover {
            background-color: #0e619f;
        }

        /* Small toggle switch for countries */
        .small-switch {
            position: relative;
            display: inline-block;
            width: 40px;
            height: 20px;
        }

        .small-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .small-slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: 0.4s;
            border-radius: 20px;
        }

        .small-slider:before {
            position: absolute;
            content: "";
            height: 14px;
            width: 14px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: 0.4s;
            border-radius: 50%;
        }

        .small-switch input:checked + .small-slider {
            background-color: #1171ba;
        }

        .small-switch input:checked + .small-slider:before {
            transform: translateX(20px);
        }

        /* Collapsible sections */
        .collapsible {
            cursor: pointer;
            padding: 8px;
            width: 100%;
            border: none;
            text-align: left;
            outline: none;
            font-weight: bold;
            background-color: #f1f1f1;
            margin-top: 5px;
            border-radius: 5px;
        }

        .collapsible:after {
            content: '\002B';
            color: #1171ba;
            font-weight: bold;
            float: right;
            margin-left: 5px;
        }

        .active:after {
            content: "\2212";
        }

        .collapsible-content {
            padding: 0 5px;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.2s ease-out;
        }

        /* Search box */
        .search-box {
            width: 100%;
            padding: 8px;
            margin-bottom: 10px;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            font-size: 14px;
        }

        /* Bulk action buttons */
        .bulk-actions {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
        }

        .bulk-button {
            padding: 5px 10px;
            background-color: #6c757d;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
        }

        .bulk-button:hover {
            background-color: #5a6268;
        }

        .bulk-button.all {
            background-color: #28a745;
        }

        .bulk-button.all:hover {
            background-color: #218838;
        }

        .bulk-button.none {
            background-color: #dc3545;
        }

        .bulk-button.none:hover {
            background-color: #c82333;
        }

        /* Button styles for new buttons */
        .btn {
            padding: 8px 15px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            margin: 5px;
            transition: all 0.3s;
        }

        .btn.save {
            background-color: #28a745;
            color: white;
        }

        .btn.delete {
            background-color: #dc3545;
            color: white;
        }

        .btn.email-list {
            background-color: #17a2b8;
            color: white;
        }

        .btn.google {
            background-color: #ffc107;
            color: #212529;
        }

        .button-container {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 20px;
        }

        .input-box {
            padding: 8px;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            font-size: 14px;
            flex-grow: 1;
        }

        .success-message {
            background-color: #28a745;
            color: white;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
            text-align: center;
            display: none;
        }
    </style>
</head>
<body>
    <h1>
        <img src="https://raw.githubusercontent.com/prakashsharma19/hosted-images/main/pphlogo.png" alt="PPH Logo">
        Advertisements-PPH
    </h1>

    <!-- Clear memory button -->
    <button class="clear-memory-button" onclick="clearMemory()">Clear Memory</button>

    <!-- User Controls in upper-right corner -->
    <div id="userControls" style="display: none;">
        <img src="https://raw.githubusercontent.com/prakashsharma19/hosted-images/main/pphlogo.png" alt="PPH Logo">
        <span id="loggedInUser"></span>
        <button id="logoutButton" onclick="logout()">Logout</button>
    </div>

    <div class="login-container">
        <input type="text" id="username" placeholder="Enter your name">
        <input type="password" id="password" placeholder="Enter your password">
        <button id="loginButton" onclick="login()">Login</button>
    </div>

    <div class="font-controls" style="display:none;">
        <div class="control-group">
            <div>
                <label>
                    <input type="radio" name="cutOption" value="keyboard" checked>
                    Keyboard
                </label>
                <label>
                    <input type="radio" name="cutOption" value="mouse">
                    Mouse
                </label>
            </div>

            <div>
                <label for="effectsToggle">Effects:</label>
                <input type="checkbox" id="effectsToggle" onchange="saveEffectPreferences()">
            </div>

            <div>
                <label for="effectType">Effect:</label>
                <select id="effectType" onchange="saveEffectPreferences()">
                    <option value="none">None</option>
                    <option value="fadeOut">Fade Out</option>
                    <option value="vanish">Vanish</option>
                    <option value="explode">Explode</option>
                </select>
            </div>

            <div>
                <label for="fontStyle">Font:</label>
                <select id="fontStyle" onchange="updateFont()">
                    <option value="Arial">Arial</option>
                    <option value="Times New Roman">Times New Roman</option>
                    <option value="Courier New">Courier New</option>
                    <option value="Georgia">Georgia</option>
                    <option value="Calibri Light">Calibri Light</option>
                </select>
            </div>

            <div>
                <label for="fontSize">Size:</label>
                <input type="number" id="fontSize" value="16" onchange="updateFont()">px
            </div>

            <div class="gap-control">
                <label for="gapOption">Gap:</label>
                <select id="gapOption" onchange="saveGapPreferences()">
                    <option value="default">Default</option>
                    <option value="nil">Nil</option>
                </select>
            </div>
        </div>
    </div>

    <div class="button-container">
        <input type="email" id="unsubscribedEmail" placeholder="Enter Unsubscribed Email" class="input-box">
        
        <button onclick="saveUnsubscribedEmail()" id="exportButton" class="btn save">
            Save
        </button>
        
        <button onclick="deleteUnsubscribedEntries()" class="btn delete">
             Delete Unsubscribed Ad ✘
        </button>
        
        <button onclick="window.open('https://docs.google.com/document/d/14AIqhs3wQ_T0hV7YNH2ToBRBH1MEkzmunw2e9WNgeo8/edit?tab=t.0', '_blank')" 
                class="btn email-list">
            Email List
        </button>
        
        <button onclick="window.open('https://docs.google.com/spreadsheets/d/10OYn06bPKVXmf__3d9Q_7kky8VHRlIKO/edit?gid=1887922208#gid=1887922208', '_blank')" class="btn google">
            Update Ad Progress
        </button>
    </div>

    <div id="successMessage" class="success-message" style="display: none;">Email saved successfully!</div>

    <div class="toggle-container">
        <label class="switch">
            <input type="checkbox" id="dearProfessorToggle" onchange="toggleDearProfessor()">
            <span class="slider round"></span>
        </label>
        <span id="dearProfessorLabel">Include "Dear Professor"</span>
    </div>

    <div class="input-container" style="display:none;">
        <div class="container-header" onclick="toggleBox('pasteBox')">
            Paste your text here
            <span id="pasteBoxToggle">[+]</span>
        </div>
        <div id="pasteBox" class="input-boxes">
            <textarea id="inputText" rows="5" placeholder="Paste your text here..."></textarea>
            <button id="okButton" onclick="processText()">Process</button>
        </div>
    </div>

    <!-- Incomplete Entries Box -->
    <div class="input-container" style="display:none;">
        <div class="container-header" onclick="toggleBox('incompleteBox')">
            Incomplete Entries/Removed Countries
            <span id="incompleteBoxToggle">[+]</span>
        </div>
        <div id="incompleteBox" class="input-boxes">
            <textarea id="incompleteText" rows="5" placeholder="Incomplete entries will be shown here..."></textarea>
            <button onclick="copyIncompleteEntries()">Copy</button>
        </div>
    </div>

    <div class="input-container" style="display:none;">
        <div class="container-header" onclick="toggleBox('roughBox')">
            Rough Work
            <span id="roughBoxToggle">[+]</span>
        </div>
        <div id="roughBox" class="input-boxes rough-container">
            <textarea id="roughText" rows="5" placeholder="Rough Work..."></textarea>
        </div>
    </div>

    <div class="top-controls" style="display:none;">
        <div id="remainingTime">File completed by: <span id="remainingTimeText"></span> (<span id="completionPercentage">0%</span>)
            <div class="hourglass"></div>
        </div>
    </div>

    <div id="adCount" style="display:none;">
        Total Advertisements: <span id="totalAds">0</span>
        <span id="loadingIndicator">Processing, please wait...</span>
    </div>
    <div id="dailyAdCount" style="display:none;">Total Ads Sent Today: 0</div>
    <div class="progress-bar-container">
        <div class="progress-bar" id="progressBar"></div>
    </div>
    <div id="countryCount" style="display:none;">
        <div class="country-filter">
            <button class="collapsible">Country Filters</button>
            <div class="collapsible-content" id="countryFilters">
                <input type="text" id="countrySearch" class="search-box" placeholder="Search countries..." onkeyup="searchCountries()">
                <div class="bulk-actions">
                    <button class="bulk-button all" onclick="toggleAllCountries(true)">All</button>
                    <button class="bulk-button none" onclick="toggleAllCountries(false)">None</button>
                </div>
                <div id="countryListContainer"></div>
            </div>
        </div>
        <div class="group-management">
            <button class="collapsible">Country Groups</button>
            <div class="collapsible-content">
                <div id="countryGroups"></div>
                <div class="group-controls">
                    <input type="text" id="newGroupName" class="group-input" placeholder="Group name">
                    <button onclick="createGroup()" class="group-button">Create Group</button>
                </div>
            </div>
        </div>
    </div>

    <div id="output" class="text-container" style="display:none;" contenteditable="true">
        <p id="cursorStart">Place your cursor here</p>
    </div>

    <div class="right-content">
        <div id="currentTime"></div>
        <div class="reminder-heading">Ad Slots:</div>
        <ul class="reminder-slots">
            <li data-time="09:00">9:00-9:30 AM</li>
            <li data-time="10:35">10:35-10:45 AM</li>
            <li data-time="11:50">11:50-12:00 PM</li>
            <li data-time="13:05">1:05-1:10 PM</li>
            <li data-time="14:20">2:20-2:30 PM</li>
            <li data-time="15:40">3:40-3:45 PM</li>
            <li data-time="16:50">4:50-5:00 PM</li>
        </ul>
        <div class="reminder-note">(Select your slots to get reminder)</div>

        <!-- Button Container -->
        <div id="rightSidebar" style="display:none;">
            <button class="fullscreen-button" onclick="toggleFullScreen()">Full Screen</button>
            <button id="undoButton" style="display:none;" onclick="undoLastCut()">Undo Last Cut</button>
            <button id="lockButton" onclick="toggleLock()">Lock</button>
        </div>
    </div>

    <div id="reminderPopup" class="popup">
        <span style="font-size: 50px;">⏰</span>
        <p>Send Ads</p>
        <button onclick="dismissPopup()">OK</button>
    </div>

    <!-- Scroll Lock Notice -->
    <div id="scrollLockNotice" class="scroll-lock-notice">Scrolling is locked. Unlock to scroll.</div>

    <!-- Credit Section -->
    <div id="credit">
        This Web-App is Developed by <a href="https://prakashsharma19.github.io/prakash/" target="_blank">Prakash</a>
    </div>
    
    <script>
        // Country list shortened for brevity - include your full country list here
        const countryList = [
            "Afghanistan", "Algeria", "Andorra", "Angola", /* ... include all your countries ... */, "Zimbabwe"
        ];

        // Performance optimized variables
        const MAX_VISIBLE_PARAGRAPHS = 50;
        const PROCESSING_CHUNK_SIZE = 100;
        const PROCESSING_DELAY = 0;
        const CUT_COOLDOWN = 50; // ms
        
        let currentUser = null;
        let dailyAdCount = 0;
        let cutHistory = [];
        let isLocked = false;
        let isProcessing = false;
        let totalParagraphs = 0;
        let cutCooldown = false;
        let countryStates = {};
        let countryGroups = {};
        let allParagraphs = [];
        let renderedParagraphs = [];
        let visibleStartIndex = 0;
        let includeDearProfessor = true;
        let worker = null;

        // Initialize web worker
        function initWorker() {
            if (window.Worker) {
                const workerCode = `
                    const highlightErrors = (text) => {
                        let modifiedText = text.replace(/\\?/g, '<span class="error">?</span>');
                        const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/;
                        
                        if (!emailRegex.test(text)) {
                            modifiedText += ' <span class="error">Missing email</span>';
                        }
                        
                        const countries = ${JSON.stringify(countryList)};
                        
                        if (!countries.some(country => text.includes(country))) {
                            modifiedText += ' <span class="error">Missing country</span>';
                        }
                        
                        return modifiedText;
                    };

                    self.onmessage = function(e) {
                        if (e.data.type === 'processChunk') {
                            const results = [];
                            const chunk = e.data.chunk;
                            
                            for (let i = 0; i < chunk.length; i++) {
                                const paragraph = chunk[i].trim();
                                if (paragraph !== '') {
                                    const lines = paragraph.split('\\n');
                                    let firstLine = lines[0].trim();
                                    
                                    if (!firstLine.startsWith('Professor')) {
                                        firstLine = 'Professor ' + firstLine;
                                        lines[0] = firstLine;
                                    }

                                    const lastName = firstLine.split(' ').pop();

                                    if (e.data.includeDearProfessor) {
                                        const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/;
                                        const emailLineIndex = lines.findIndex(line => emailRegex.test(line));
                                        if (emailLineIndex !== -1) {
                                            const greeting = 'Dear Professor ' + lastName + ',';
                                            if (e.data.gapOption === 'nil') {
                                                lines.splice(emailLineIndex + 1, 0, greeting);
                                            } else {
                                                lines.splice(emailLineIndex + 1, 0, '', greeting);
                                            }
                                        }
                                    }

                                    const text = lines.join('\\n');
                                    const html = highlightErrors(text.replace(/\\n/g, '<br>'));
                                    const hasError = html.includes('error');
                                    
                                    results.push({
                                        index: e.data.index + i,
                                        text: text,
                                        html: html,
                                        hasError: hasError,
                                        isRussia: paragraph.includes('Russia')
                                    });
                                }
                            }
                            
                            self.postMessage({
                                type: 'processedChunk',
                                processed: results,
                                isLast: e.data.isLast
                            });
                        }
                    };
                `;

                const blob = new Blob([workerCode], { type: 'application/javascript' });
                worker = new Worker(URL.createObjectURL(blob));
                
                worker.onmessage = function(e) {
                    if (e.data.type === 'processedChunk') {
                        processWorkerResponse(e.data);
                    }
                };
            }
        }

        // Process worker response
        function processWorkerResponse(data) {
            const incompleteContainer = document.getElementById('incompleteText');
            
            data.processed.forEach(item => {
                if (item.hasError) {
                    incompleteContainer.value += item.text.replace(/<br>/g, '\n').replace(/<[^>]+>/g, '') + '\n\n';
                } else {
                    allParagraphs[item.index] = {
                        id: item.index,
                        html: item.html,
                        text: item.text,
                        isRussia: item.isRussia
                    };
                }
            });
            
            if (data.isLast) {
                finalizeProcessing();
            }
        }

        // Initialize country states and groups from localStorage
        function initializeCountryStates() {
            const savedStates = localStorage.getItem(`countryStates_${currentUser}`);
            if (savedStates) {
                countryStates = JSON.parse(savedStates);
            } else {
                countryList.forEach(country => {
                    countryStates[country] = true;
                });
            }
        }

        function initializeCountryGroups() {
            const savedGroups = localStorage.getItem(`countryGroups_${currentUser}`);
            if (savedGroups) {
                countryGroups = JSON.parse(savedGroups);
            } else {
                countryGroups = {
                    "Asia": ["India", "China", "Japan", "South Korea", "Singapore", "Thailand", "Vietnam", "Indonesia", "Malaysia", "Philippines"],
                    "Europe": ["France", "Germany", "Italy", "Spain", "United Kingdom", "UK", "U.K.", "Switzerland", "Netherlands", "Belgium"],
                    "Middle East": ["Saudi Arabia", "UAE", "U.A.E.", "Qatar", "Kuwait", "Oman", "Bahrain", "Israel"],
                    "Africa": ["South Africa", "Egypt", "Nigeria", "Kenya", "Ghana", "Morocco", "Tunisia"],
                    "Americas": ["United States", "USA", "U.S.A.", "Canada", "Brazil", "Brasil", "Mexico", "Argentina", "Chile", "Colombia"]
                };
            }
        }

        function saveCountryStates() {
            if (currentUser) {
                localStorage.setItem(`countryStates_${currentUser}`, JSON.stringify(countryStates));
            }
        }

        function saveCountryGroups() {
            if (currentUser) {
                localStorage.setItem(`countryGroups_${currentUser}`, JSON.stringify(countryGroups));
            }
        }

        function renderCountryFilters() {
            const container = document.getElementById('countryListContainer');
            container.innerHTML = '';

            const sortedCountries = Object.keys(countryStates).sort((a, b) => a.localeCompare(b));
            const countryCounts = countCountryOccurrences();

            sortedCountries.forEach(country => {
                const countryItem = document.createElement('div');
                countryItem.className = 'country-item';

                const toggle = document.createElement('label');
                toggle.className = 'small-switch';
                toggle.innerHTML = `
                    <input type="checkbox" ${countryStates[country] ? 'checked' : ''} onchange="toggleCountry('${country}', this.checked)">
                    <span class="small-slider"></span>
                `;

                const name = document.createElement('span');
                name.className = 'country-name';
                name.textContent = country;

                const count = document.createElement('span');
                count.className = 'country-count';
                count.textContent = `(${countryCounts[country] || 0})`;

                countryItem.appendChild(toggle);
                countryItem.appendChild(name);
                countryItem.appendChild(count);
                container.appendChild(countryItem);
            });
        }

        function renderCountryGroups() {
            const container = document.getElementById('countryGroups');
            container.innerHTML = '';

            Object.keys(countryGroups).forEach(groupName => {
                const groupItem = document.createElement('div');
                groupItem.className = 'group-item';

                const toggle = document.createElement('label');
                toggle.className = 'small-switch';
                toggle.innerHTML = `
                    <input type="checkbox" checked onchange="toggleGroup('${groupName}', this.checked)">
                    <span class="small-slider"></span>
                `;

                const name = document.createElement('div');
                name.className = 'group-name';
                name.textContent = groupName;

                const countries = document.createElement('div');
                countries.className = 'group-countries';
                countries.textContent = countryGroups[groupName].join(', ');

                const groupControls = document.createElement('div');
                groupControls.className = 'group-controls';
                groupControls.innerHTML = `
                    <button onclick="editGroup('${groupName}')" class="group-button">Edit</button>
                    <button onclick="deleteGroup('${groupName}')" class="group-button">Delete</button>
                `;

                groupItem.appendChild(toggle);
                groupItem.appendChild(name);
                groupItem.appendChild(countries);
                groupItem.appendChild(groupControls);
                container.appendChild(groupItem);
            });
        }

        function toggleCountry(country, enabled) {
            countryStates[country] = enabled;
            saveCountryStates();
            filterCountries();
        }

        function toggleAllCountries(enable) {
            for (const country in countryStates) {
                countryStates[country] = enable;
            }
            saveCountryStates();
            renderCountryFilters();
            filterCountries();
        }

        function toggleGroup(groupName, enabled) {
            countryGroups[groupName].forEach(country => {
                if (countryStates.hasOwnProperty(country)) {
                    countryStates[country] = enabled;
                }
            });
            saveCountryStates();
            renderCountryFilters();
            filterCountries();
        }

        function createGroup() {
            const groupName = document.getElementById('newGroupName').value.trim();
            if (groupName && !countryGroups[groupName]) {
                countryGroups[groupName] = [];
                saveCountryGroups();
                renderCountryGroups();
                document.getElementById('newGroupName').value = '';
            }
        }

        function editGroup(groupName) {
            const newName = prompt("Enter new group name:", groupName);
            if (newName && newName !== groupName) {
                countryGroups[newName] = countryGroups[groupName];
                delete countryGroups[groupName];
                saveCountryGroups();
                renderCountryGroups();
            }
            
            const newCountries = prompt("Edit countries (comma separated):", countryGroups[groupName].join(', '));
            if (newCountries !== null) {
                countryGroups[groupName] = newCountries.split(',').map(c => c.trim()).filter(c => c);
                saveCountryGroups();
                renderCountryGroups();
            }
        }

        function deleteGroup(groupName) {
            if (confirm(`Are you sure you want to delete the group "${groupName}"?`)) {
                delete countryGroups[groupName];
                saveCountryGroups();
                renderCountryGroups();
            }
        }

        function searchCountries() {
            const searchTerm = document.getElementById('countrySearch').value.toLowerCase();
            const countryItems = document.querySelectorAll('.country-item');
            
            countryItems.forEach(item => {
                const countryName = item.querySelector('.country-name').textContent.toLowerCase();
                if (countryName.includes(searchTerm)) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        }

        function filterCountries() {
            const outputContainer = document.getElementById('output');
            const paragraphs = outputContainer.querySelectorAll('p');
            
            paragraphs.forEach(paragraph => {
                let shouldShow = false;
                const text = paragraph.innerText;
                
                for (const country in countryStates) {
                    if (countryStates[country] && text.includes(country)) {
                        shouldShow = true;
                        break;
                    }
                }
                
                if (!shouldShow && !Object.values(countryStates).some(state => state)) {
                    shouldShow = true;
                }
                
                paragraph.style.display = shouldShow ? 'block' : 'none';
            });
            
            updateCounts();
        }

        function showSuccessMessage(message) {
            const successMessage = document.getElementById('successMessage');
            successMessage.innerText = message;
            successMessage.style.display = 'block';

            setTimeout(() => {
                successMessage.style.display = 'none';
            }, 3000);
        }

        function saveText() {
            const inputText = document.getElementById('inputText').value;
            const roughText = document.getElementById('roughText').value;
            const outputText = document.getElementById('output').innerHTML;
            const incompleteText = document.getElementById('incompleteText').value;
            if (currentUser) {
                localStorage.setItem(`savedInput_${currentUser}`, inputText);
                localStorage.setItem(`savedRough_${currentUser}`, roughText);
                localStorage.setItem(`savedOutput_${currentUser}`, outputText);
                localStorage.setItem(`savedIncomplete_${currentUser}`, incompleteText);
                localStorage.setItem(`dailyAdCount_${currentUser}`, dailyAdCount);
                localStorage.setItem(`lastCutTime_${currentUser}`, Date.now());
                localStorage.setItem(`totalParagraphs_${currentUser}`, totalParagraphs);
                saveSelectedReminders();
                saveEffectPreferences();
                saveOperationPreferences();
                saveFontPreferences();
                saveGapPreferences();
                saveCountryStates();
                saveCountryGroups();
            }
        }

        function loadText() {
            if (currentUser) {
                const savedInput = localStorage.getItem(`savedInput_${currentUser}`);
                const savedRough = localStorage.getItem(`savedRough_${currentUser}`);
                const savedOutput = localStorage.getItem(`savedOutput_${currentUser}`);
                const savedIncomplete = localStorage.getItem(`savedIncomplete_${currentUser}`);
                const savedDailyAdCount = localStorage.getItem(`dailyAdCount_${currentUser}`);
                const lastCutTime = localStorage.getItem(`lastCutTime_${currentUser}`);
                const savedTotalParagraphs = localStorage.getItem(`totalParagraphs_${currentUser}`);
                const savedFontStyle = localStorage.getItem(`fontStyle_${currentUser}`);
                const savedFontSize = localStorage.getItem(`fontSize_${currentUser}`);
                const savedGapOption = localStorage.getItem(`gapOption_${currentUser}`);
                
                if (savedInput) document.getElementById('inputText').value = savedInput;
                if (savedRough) document.getElementById('roughText').value = savedRough;
                if (savedOutput) document.getElementById('output').innerHTML = savedOutput;
                if (savedIncomplete) document.getElementById('incompleteText').value = savedIncomplete;
                
                if (savedDailyAdCount && lastCutTime) {
                    const lastCutDate = new Date(parseInt(lastCutTime, 10));
                    const currentDate = new Date();
                    if (lastCutDate.toDateString() === currentDate.toDateString()) {
                        dailyAdCount = parseInt(savedDailyAdCount, 10);
                    }
                }
                
                if (savedTotalParagraphs) totalParagraphs = parseInt(savedTotalParagraphs, 10);
                if (savedFontStyle) document.getElementById('fontStyle').value = savedFontStyle;
                if (savedFontSize) document.getElementById('fontSize').value = savedFontSize;
                if (savedGapOption) document.getElementById('gapOption').value = savedGapOption;
                
                loadEffectPreferences();
                loadOperationPreferences();
                loadSelectedReminders();
                initializeCountryStates();
                initializeCountryGroups();
                updateCounts();
                updateFont();
                renderCountryFilters();
                renderCountryGroups();
                document.getElementById('rightSidebar').style.display = 'block';
                document.getElementById('lockButton').style.display = 'inline-block';
            }
        }

        function saveFontPreferences() {
            const fontStyle = document.getElementById('fontStyle').value;
            const fontSize = document.getElementById('fontSize').value;
            if (currentUser) {
                localStorage.setItem(`fontStyle_${currentUser}`, fontStyle);
                localStorage.setItem(`fontSize_${currentUser}`, fontSize);
            }
        }

        function countCountryOccurrences() {
            const counts = {};
            allParagraphs.forEach(p => {
                if (!p) return;
                countryList.forEach(country => {
                    if (p.text.includes(country)) {
                        counts[country] = (counts[country] || 0) + 1;
                    }
                });
            });
            return counts;
        }

        function highlightErrors(text) {
            let modifiedText = text.replace(/\?/g, '<span class="error">?</span>');
            if (!text.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/)) {
                modifiedText += ' <span class="error">Missing email</span>';
            }
            if (!countryList.some(country => text.includes(country))) {
                modifiedText += ' <span class="error">Missing country</span>';
            }
            return modifiedText;
        }

        function updateCounts() {
            let adCount = 0;
            allParagraphs.forEach(p => {
                if (p) {
                    const firstLine = p.text.split('\n')[0];
                    if (firstLine.startsWith('To') || firstLine.startsWith('Professor')) {
                        adCount += 1;
                    }
                }
            });

            document.getElementById('totalAds').innerText = adCount;
            document.getElementById('dailyAdCount').innerText = `Total Ads Today: ${dailyAdCount}`;
            
            updateProgressBar(dailyAdCount);
            updateRemainingTime(dailyAdCount);
        }

        function updateProgressBar(dailyAdCount) {
            const progressBar = document.getElementById('progressBar');
            const maxCount = 5000;
            const percentage = Math.min(dailyAdCount / maxCount, 1) * 100;
            progressBar.style.width = `${percentage}%`;

            const red = Math.max(255 - Math.floor((dailyAdCount / maxCount) * 255), 0);
            const green = Math.min(Math.floor((dailyAdCount / maxCount) * 255), 255);
            progressBar.style.backgroundColor = `rgb(${red},${green},0)`;
        }

        function updateRemainingTime(dailyAdCount) {
            const remainingEntries = totalParagraphs - dailyAdCount;
            const remainingTimeInMinutes = remainingEntries / 25;
            const remainingTimeInSeconds = remainingTimeInMinutes * 60;
            const hours = Math.floor(remainingTimeInSeconds / 3600);
            const minutes = Math.floor((remainingTimeInSeconds % 3600) / 60);

            const percentageCompleted = Math.min((dailyAdCount / totalParagraphs) * 100, 100).toFixed(2);

            document.getElementById('remainingTimeText').innerText = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
            document.getElementById('completionPercentage').innerText = `${percentageCompleted}%`;
        }

        // Initialize the toggle state from localStorage
        document.addEventListener('DOMContentLoaded', () => {
            const savedState = localStorage.getItem('includeDearProfessor');
            if (savedState !== null) {
                includeDearProfessor = savedState === 'true';
                document.getElementById('dearProfessorToggle').checked = includeDearProfessor;
                updateToggleLabel();
            }
            
            // Initialize collapsible sections
            const coll = document.getElementsByClassName("collapsible");
            for (let i = 0; i < coll.length; i++) {
                coll[i].addEventListener("click", function() {
                    this.classList.toggle("active");
                    const content = this.nextElementSibling;
                    if (content.style.maxHeight) {
                        content.style.maxHeight = null;
                    } else {
                        content.style.maxHeight = content.scrollHeight + "px";
                    } 
                });
            }
            
            // Initialize web worker
            initWorker();
        });

        function toggleDearProfessor() {
            includeDearProfessor = document.getElementById('dearProfessorToggle').checked;
            localStorage.setItem('includeDearProfessor', includeDearProfessor);
            updateToggleLabel();
        }

        function updateToggleLabel() {
            const label = document.getElementById('dearProfessorLabel');
            label.innerText = includeDearProfessor ? '✔ "Dear Professor"' : '✘ "Dear Professor"';
        }

        function processText() {
            if (isProcessing) return;
            
            isProcessing = true;
            document.getElementById('loadingIndicator').style.display = 'inline';
            
            const inputText = document.getElementById('inputText').value;
            const paragraphs = inputText.split(/\n\s*\n/);
            totalParagraphs = paragraphs.length;
            
            // Clear existing content
            const outputContainer = document.getElementById('output');
            outputContainer.innerHTML = '<p id="cursorStart">Place your cursor here</p>';
            document.getElementById('incompleteText').value = '';
            
            // Reset data structures
            allParagraphs = [];
            renderedParagraphs = [];
            visibleStartIndex = 0;
            
            // Process in chunks using web worker if available
            if (worker) {
                const chunkSize = 1000;
                for (let i = 0; i < paragraphs.length; i += chunkSize) {
                    const chunk = paragraphs.slice(i, i + chunkSize);
                    worker.postMessage({
                        type: 'processChunk',
                        chunk: chunk,
                        includeDearProfessor: includeDearProfessor,
                        gapOption: document.getElementById('gapOption').value,
                        index: i,
                        isLast: (i + chunkSize >= paragraphs.length)
                    });
                }
            } else {
                // Fallback to main thread processing
                processChunkMainThread(paragraphs, 0);
            }
        }

        // Main thread processing fallback
        function processChunkMainThread(paragraphs, startIndex) {
            const chunkSize = PROCESSING_CHUNK_SIZE;
            const endIndex = Math.min(startIndex + chunkSize, paragraphs.length);
            const incompleteContainer = document.getElementById('incompleteText');
            
            for (let i = startIndex; i < endIndex; i++) {
                let paragraph = paragraphs[i].trim();
                if (paragraph !== '') {
                    const processed = processSingleParagraph(paragraph);
                    
                    if (processed.hasError) {
                        incompleteContainer.value += processed.text + '\n\n';
                    } else {
                        allParagraphs[i] = {
                            id: i,
                            html: processed.html,
                            text: processed.text,
                            isRussia: processed.isRussia
                        };
                    }
                }
            }
            
            if (endIndex < paragraphs.length) {
                setTimeout(() => processChunkMainThread(paragraphs, endIndex), PROCESSING_DELAY);
            } else {
                finalizeProcessing();
            }
        }

        // Process single paragraph (reusable function)
        function processSingleParagraph(paragraph) {
            const lines = paragraph.split('\n');
            let firstLine = lines[0].trim();
            const result = {
                hasError: false,
                isRussia: false,
                text: '',
                html: ''
            };

            // Ensure the first line starts with "Professor"
            if (!firstLine.startsWith('Professor')) {
                firstLine = `Professor ${firstLine}`;
                lines[0] = firstLine;
            }

            let lastName = firstLine.split(' ').pop();

            if (includeDearProfessor) {
                const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/;
                const emailLineIndex = lines.findIndex(line => emailRegex.test(line));
                if (emailLineIndex !== -1) {
                    const greeting = `Dear Professor ${lastName},`;
                    if (document.getElementById('gapOption').value === 'nil') {
                        lines.splice(emailLineIndex + 1, 0, greeting);
                    } else {
                        lines.splice(emailLineIndex + 1, 0, '', greeting);
                    }
                }
            }

            result.text = lines.join('\n');
            result.html = highlightErrors(result.text.replace(/\n/g, '<br>'));
            result.hasError = result.html.includes('error');
            result.isRussia = paragraph.includes('Russia');
            
            return result;
        }

        // Finalize processing
        function finalizeProcessing() {
            // Sort allParagraphs (Russia last)
            allParagraphs.sort((a, b) => {
                if (!a || !b) return 0;
                if (a.isRussia && !b.isRussia) return 1;
                if (!a.isRussia && b.isRussia) return -1;
                return a.id - b.id;
            });

            // Render initial visible paragraphs
            renderVisibleParagraphs();
            
            updateCounts();
            saveText();
            document.getElementById('lockButton').style.display = 'inline-block';
            document.getElementById('loadingIndicator').style.display = 'none';

            // Automatically delete unsubscribed entries
            const deletedCount = deleteUnsubscribedEntries();
            
            if (deletedCount > 0) {
                showPopupNotification(`Deleted ${deletedCount} unsubscribed entries.`);
            }
            
            filterCountries();
            isProcessing = false;
        }

        // Render only visible paragraphs
        function renderVisibleParagraphs() {
            const outputContainer = document.getElementById('output');
            const fragment = document.createDocumentFragment();
            
            // Clear existing rendered paragraphs
            renderedParagraphs.forEach(p => {
                if (p.parentNode === outputContainer) {
                    outputContainer.removeChild(p);
                }
            });
            renderedParagraphs = [];
            
            // Determine visible range
            const start = Math.max(0, visibleStartIndex);
            const end = Math.min(allParagraphs.length, visibleStartIndex + MAX_VISIBLE_PARAGRAPHS);
            
            // Create new paragraphs
            for (let i = start; i < end; i++) {
                if (!allParagraphs[i]) continue;
                
                const p = document.createElement('p');
                p.innerHTML = allParagraphs[i].html;
                p.dataset.id = allParagraphs[i].id;
                fragment.appendChild(p);
                renderedParagraphs.push(p);
            }
            
            outputContainer.appendChild(fragment);
        }

        // Optimized cutParagraph function
        function cutParagraph(paragraph) {
            if (cutCooldown || !paragraph) return;
            
            // Use requestAnimationFrame for smoother performance
            requestAnimationFrame(() => {
                const paragraphId = parseInt(paragraph.dataset.id);
                const paragraphIndex = allParagraphs.findIndex(p => p && p.id === paragraphId);
                
                if (paragraphIndex === -1) return;
                
                const textToCopy = allParagraphs[paragraphIndex].text;
                cutHistory.push({
                    text: textToCopy,
                    index: paragraphIndex,
                    element: paragraph
                });

                const effectType = document.getElementById('effectType').value;
                const effectsEnabled = document.getElementById('effectsToggle').checked;
                const textToProcess = textToCopy.replace(/^To\n/, '');

                // Use CSS transforms for animation
                if (effectsEnabled && effectType !== 'none') {
                    paragraph.style.transition = 'all 0.1s ease-out';
                    
                    switch(effectType) {
                        case 'fadeOut':
                            paragraph.style.opacity = '0';
                            break;
                        case 'vanish':
                            paragraph.style.transform = 'scale(0)';
                            break;
                        case 'explode':
                            paragraph.style.transform = 'scale(3)';
                            paragraph.style.opacity = '0';
                            break;
                    }
                    
                    // Remove after animation
                    setTimeout(() => {
                        removeParagraph(paragraphIndex, textToProcess);
                    }, 100);
                } else {
                    // Immediate removal
                    removeParagraph(paragraphIndex, textToProcess);
                }
            });
            
            // Set minimal cooldown
            cutCooldown = true;
            setTimeout(() => { cutCooldown = false; }, CUT_COOLDOWN);
        }

        // Optimized paragraph removal
        function removeParagraph(index, textToProcess) {
            // Remove from our data structure
            allParagraphs.splice(index, 1);
            
            // Update the input text
            const inputText = document.getElementById('inputText').value;
            document.getElementById('inputText').value = inputText.replace(textToProcess.split('\nDear Professor')[0], '').trim();
            
            // Update counters
            dailyAdCount++;
            updateCounts();
            saveText();
            
            // Re-render visible paragraphs
            renderVisibleParagraphs();
            
            // Show undo button
            document.getElementById('undoButton').style.display = 'block';
            
            // Copy to clipboard
            copyToClipboard(textToProcess);
            
            // Focus output
            document.getElementById('output').focus();
        }

        // Optimized clipboard copy
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).catch(err => {
                // Fallback for older browsers
                const textarea = document.createElement('textarea');
                textarea.value = text;
                textarea.style.position = 'fixed';
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
            });
        }

        // Optimized undoLastCut
        function undoLastCut() {
            if (cutHistory.length === 0) return;
            
            const lastCut = cutHistory.pop();
            
            // Restore to data structure
            allParagraphs.splice(lastCut.index, 0, {
                id: lastCut.index,
                html: lastCut.element.innerHTML,
                text: lastCut.text,
                isRussia: lastCut.text.includes('Russia')
            });
            
            // Restore to input text
            const inputText = document.getElementById('inputText').value;
            document.getElementById('inputText').value = `${lastCut.text}\n\n${inputText}`.trim();
            
            // Update counters
            dailyAdCount--;
            updateCounts();
            saveText();
            
            // Re-render
            renderVisibleParagraphs();
            
            if (cutHistory.length === 0) {
                document.getElementById('undoButton').style.display = 'none';
            }
        }

        function handleCursorMovement(event) {
            if (isLocked) return;
            
            const selection = window.getSelection();
            if (selection.rangeCount > 0) {
                const range = selection.getRangeAt(0);
                const container = range.commonAncestorContainer;

                let paragraph = container;
                while (paragraph && paragraph.nodeName !== 'P') {
                    paragraph = paragraph.parentNode;
                }

                if (paragraph && paragraph.textContent.includes('Professor')) {
                    cutParagraph(paragraph);
                    document.getElementById('output').focus();
                }
            }
        }

        function handleMouseClick(event) {
            if (isLocked) return;
            
            const cutOption = document.querySelector('input[name="cutOption"]:checked').value;
            if (cutOption === 'mouse') {
                handleCursorMovement(event);
            }
        }

        function startMonitoring() {
            const cutOption = document.querySelector('input[name="cutOption"]:checked').value;
            if (cutOption === 'keyboard') {
                document.addEventListener('keyup', handleCursorMovement);
            } else {
                document.removeEventListener('keyup', handleCursorMovement);
            }
        }

        function updateFont() {
            const fontStyle = document.getElementById('fontStyle').value;
            const fontSize = document.getElementById('fontSize').value;
            document.getElementById('output').style.fontFamily = fontStyle;
            document.getElementById('output').style.fontSize = `${fontSize}px`;
            saveFontPreferences();
        }

        function saveGapPreferences() {
            const gapOption = document.getElementById('gapOption').value;
            if (currentUser) {
                localStorage.setItem(`gapOption_${currentUser}`, gapOption);
            }
        }

        function toggleLock() {
            const lockButton = document.getElementById('lockButton');
            const interactiveElements = document.querySelectorAll('input, button, textarea, select');
            isLocked = !isLocked;

            if (isLocked) {
                lockButton.innerHTML = 'Unlock';
                lockButton.classList.add('locked');
                interactiveElements.forEach(element => {
                    if (element.id !== 'output' && element.id !== 'undoButton' && element.id !== 'lockButton') {
                        element.disabled = true;
                    }
                });
                document.body.classList.add('scroll-locked');
            } else {
                lockButton.innerHTML = 'Lock';
                lockButton.classList.remove('locked');
                interactiveElements.forEach(element => {
                    if (element.id !== 'output' && element.id !== 'undoButton' && element.id !== 'lockButton') {
                        element.disabled = false;
                    }
                });
                document.body.classList.remove('scroll-locked');
            }
        }

        function toggleBox(boxId) {
            const box = document.getElementById(boxId);
            const toggleSymbol = document.getElementById(boxId + 'Toggle');

            if (box.style.display === 'none' || box.style.display === '') {
                box.style.display = 'block';
                toggleSymbol.innerText = '[-]';
            } else {
                box.style.display = 'none';
                toggleSymbol.innerText = '[+]';
            }
        }

        function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            if (username && password) {
                currentUser = `${username}_${password}`;
                document.querySelector('.login-container').style.display = 'none';
                document.querySelector('.font-controls').style.display = 'block';
                document.querySelectorAll('.input-container').forEach(container => container.style.display = 'block');
                document.querySelector('.top-controls').style.display = 'flex';
                document.getElementById('adCount').style.display = 'block';
                document.getElementById('dailyAdCount').style.display = 'block';
                document.getElementById('remainingTime').style.display = 'block';
                document.getElementById('countryCount').style.display = 'block';
                document.getElementById('output').style.display = 'block';
                document.getElementById('userControls').style.display = 'flex';
                document.getElementById('loggedInUser').innerText = username;
                loadText();
            } else {
                alert('Please enter both username and password.');
            }
        }

        function logout() {
            currentUser = null;
            document.querySelector('.login-container').style.display = 'block';
            document.querySelector('.font-controls').style.display = 'none';
            document.querySelectorAll('.input-container').forEach(container => container.style.display = 'none');
            document.querySelector('.top-controls').style.display = 'none';
            document.getElementById('adCount').style.display = 'none';
            document.getElementById('dailyAdCount').style.display = 'none';
            document.getElementById('remainingTime').style.display = 'none';
            document.getElementById('countryCount').style.display = 'none';
            document.getElementById('output').style.display = 'none';
            document.getElementById('userControls').style.display = 'none';
        }

        document.getElementById('output').addEventListener('click', function(event) {
            if (event.target.id === 'cursorStart') {
                startMonitoring();
            } else {
                handleMouseClick(event);
            }
        });

        document.querySelectorAll('input[name="cutOption"]').forEach(option => {
            option.addEventListener('change', saveOperationPreferences);
        });

        function checkDailyReset() {
            const now = new Date();
            const lastCutTime = localStorage.getItem(`lastCutTime_${currentUser}`);
            if (lastCutTime) {
                const lastCutDate = new Date(parseInt(lastCutTime, 10));
                if (lastCutDate.toDateString() !== now.toDateString()) {
                    dailyAdCount = 0;
                    localStorage.setItem(`dailyAdCount_${currentUser}`, dailyAdCount);
                }
            }
        }

        setInterval(checkDailyReset, 60000);

        // Function to display the current time
        function updateTime() {
            const now = new Date();
            const hours = now.getHours().toString().padStart(2, '0');
            const minutes = now.getMinutes().toString().padStart(2, '0');
            const seconds = now.getSeconds().toString().padStart(2, '0');
            document.getElementById('currentTime').textContent = `${hours}:${minutes}:${seconds}`;
        }

        // Update time every second
        setInterval(updateTime, 1000);

        // Function to check if the selected time slot matches the current time
        function checkReminders() {
            const now = new Date();
            const currentTime = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;

            document.querySelectorAll('.reminder-slots li.selected').forEach(slot => {
                if (slot.dataset.time === currentTime) {
                    showPopup();
                    showNotification('Ad Reminder', `It's time to send ads for ${slot.dataset.time}`);
                    blinkBrowserIcon();
                }
            });
        }

        // Check reminders every minute
        setInterval(checkReminders, 60000);

        // Show the reminder popup
        function showPopup() {
            document.getElementById('reminderPopup').style.display = 'block';
            blinkTab();
        }

        // Dismiss the reminder popup
        function dismissPopup() {
            document.getElementById('reminderPopup').style.display = 'none';
            document.title = originalTitle;
            clearInterval(blinkInterval);
        }

        // Handle slot selection and saving
        document.querySelectorAll('.reminder-slots li').forEach(slot => {
            slot.addEventListener('click', () => {
                slot.classList.toggle('selected');
                saveSelectedReminders();
            });
        });

        function saveSelectedReminders() {
            const selectedSlots = [];
            document.querySelectorAll('.reminder-slots li.selected').forEach(slot => {
                selectedSlots.push(slot.dataset.time);
            });
            localStorage.setItem(`selectedReminders_${currentUser}`, JSON.stringify(selectedSlots));
        }

        function loadSelectedReminders() {
            const savedSlots = localStorage.getItem(`selectedReminders_${currentUser}`);
            if (savedSlots) {
                const selectedSlots = JSON.parse(savedSlots);
                document.querySelectorAll('.reminder-slots li').forEach(slot => {
                    if (selectedSlots.includes(slot.dataset.time)) {
                        slot.classList.add('selected');
                    }
                });
            }
        }

        // Blink tab title when minimized
        let originalTitle = document.title;
        let blinkInterval;

        function blinkTab() {
            let isOriginalTitle = true;
            blinkInterval = setInterval(() => {
                document.title = isOriginalTitle ? '?? Reminder: Send Ads!' : originalTitle;
                isOriginalTitle = !isOriginalTitle;
            }, 1000);
        }

        // Toggle Fullscreen Mode
        function toggleFullScreen() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen();
                document.querySelector('.fullscreen-button').textContent = 'Normal Screen';
            } else if (document.exitFullscreen) {
                document.exitFullscreen();
                document.querySelector('.fullscreen-button').textContent = 'Full Screen';
            }
        }

        // Show Desktop Notification
        function showNotification(title, body) {
            if (Notification.permission === 'granted') {
                new Notification(title, { body });
            } else if (Notification.permission !== 'denied') {
                Notification.requestPermission().then(permission => {
                    if (permission === 'granted') {
                        new Notification(title, { body });
                    }
                });
            }
        }

        // Blink browser icon
        function blinkBrowserIcon() {
            if (document.hidden) {
                const favicon = document.querySelector('link[rel="icon"]');
                const originalIcon = favicon.href;
                let isOriginalIcon = true;
                const attentionIcon = 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/Alarm_bell.png/600px-Alarm_bell.png';

                const blinkFavicon = setInterval(() => {
                    favicon.href = isOriginalIcon ? attentionIcon : originalIcon;
                    isOriginalIcon = !isOriginalIcon;
                }, 500);

                document.addEventListener('visibilitychange', () => {
                    if (!document.hidden) {
                        clearInterval(blinkFavicon);
                        favicon.href = originalIcon;
                    }
                });
            }
        }

        // Request Notification permission on page load
        document.addEventListener('DOMContentLoaded', () => {
            if (Notification.permission !== 'granted') {
                Notification.requestPermission();
            }
        });

        // Copy incomplete entries to clipboard
        function copyIncompleteEntries() {
            const incompleteText = document.getElementById('incompleteText').value;
            const tempTextarea = document.createElement('textarea');
            tempTextarea.style.position = 'fixed';
            tempTextarea.style.opacity = '0';
            tempTextarea.value = incompleteText;
            document.body.appendChild(tempTextarea);
            tempTextarea.select();
            document.execCommand('copy');
            document.body.removeChild(tempTextarea);
            alert('Incomplete entries copied to clipboard!');
        }

        // Handle scrolling lock and display notice
        document.addEventListener('wheel', function(event) {
            if (isLocked) {
                event.preventDefault();
                const scrollLockNotice = document.getElementById('scrollLockNotice');
                scrollLockNotice.style.display = 'block';
                setTimeout(() => {
                    scrollLockNotice.style.display = 'none';
                }, 2000);
            }
        }, { passive: false });

        function saveEffectPreferences() {
            const effectsEnabled = document.getElementById('effectsToggle').checked;
            const effectType = document.getElementById('effectType').value;
            if (currentUser) {
                localStorage.setItem(`effectsEnabled_${currentUser}`, effectsEnabled);
                localStorage.setItem(`effectType_${currentUser}`, effectType);
            }
        }

        function loadEffectPreferences() {
            const savedEffectsEnabled = localStorage.getItem(`effectsEnabled_${currentUser}`);
            const savedEffectType = localStorage.getItem(`effectType_${currentUser}`);
            if (savedEffectsEnabled) {
                document.getElementById('effectsToggle').checked = savedEffectsEnabled === 'true';
            }
            if (savedEffectType) {
                document.getElementById('effectType').value = savedEffectType;
            }
        }

        function saveOperationPreferences() {
            const selectedOption = document.querySelector('input[name="cutOption"]:checked').value;
            if (currentUser) {
                localStorage.setItem(`operationMode_${currentUser}`, selectedOption);
            }
        }

        function loadOperationPreferences() {
            const savedOperationMode = localStorage.getItem(`operationMode_${currentUser}`);
            if (savedOperationMode) {
                document.querySelector(`input[name="cutOption"][value="${savedOperationMode}"]`).checked = true;
            }
        }

        function showPopupNotification(message) {
            const popup = document.createElement('div');
            popup.style.cssText = `
                position: fixed;
                top: 20%;
                left: 50%;
                transform: translate(-50%, -50%);
                background-color: #1171ba;
                color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
                z-index: 1000;
                text-align: center;
                font-size: 18px;
                font-weight: bold;
            `;
            popup.innerText = message;

            const closeButton = document.createElement('button');
            closeButton.innerText = 'OK';
            closeButton.style.cssText = `
                margin-top: 10px;
                padding: 10px 20px;
                background-color: white;
                color: #1171ba;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            `;
            closeButton.onclick = () => {
                popup.remove();
            };

            popup.appendChild(closeButton);
            document.body.appendChild(popup);
        }

        function clearMemory() {
            const password = prompt('Please enter the password to clear memory, unsubscribed email data will also be deleted:');
            if (password === 'cleanall0') {
                localStorage.clear();
                alert('Memory cleared!');
            } else {
                alert('Incorrect password. Memory not cleared.');
            }
        }

        function saveUnsubscribedEmail() {
            const email = document.getElementById('unsubscribedEmail').value.trim().toLowerCase();
            if (email) {
                addUnsubscribedEmail(email);
                document.getElementById('unsubscribedEmail').value = '';
                showSuccessMessage('Email saved successfully!');
                processText();
            }
        }

        function addUnsubscribedEmail(email) {
            const emails = JSON.parse(localStorage.getItem('permanentUnsubscribedEmails')) || [];
            if (!emails.includes(email)) {
                emails.push(email);
                localStorage.setItem('permanentUnsubscribedEmails', JSON.stringify(emails));
            }
        }

        function deleteUnsubscribedEntries() {
            const unsubscribedEmails = JSON.parse(localStorage.getItem('permanentUnsubscribedEmails')) || [];
            let deletedCount = 0;

            allParagraphs = allParagraphs.filter(p => {
                if (!p) return true;
                
                let shouldKeep = true;
                unsubscribedEmails.forEach(email => {
                    if (p.text.includes(email)) {
                        shouldKeep = false;
                        deletedCount++;
                    }
                });
                return shouldKeep;
            });

            renderVisibleParagraphs();
            saveText();
            return deletedCount;
        }
    </script>
</body>
</html>
