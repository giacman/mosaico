/**
 * Mosaico Google Sheets Add-on
 * AI Content Creation Co-Pilot
 * 
 * This add-on connects to the Mosaico FastAPI backend
 * to provide AI-powered content generation directly in Sheets
 */

// --- CONFIGURATION ---
// The backend URL is now managed via Script Properties.
// Use the "Mosaico > Set Backend URL" menu to change it.
var DEFAULT_BACKEND_URL = 'https://beckham-odontographic-siu.ngrok-free.dev';

/**
 * Runs when the add-on is installed
 */
function onInstall(e) {
  onOpen(e);
}

/**
 * Runs when the spreadsheet is opened
 * Adds Mosaico menu to the UI
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Mosaico AI')
    .addItem('Generate', 'showSidebar')
    .addSeparator()
    .addItem('Set Backend URL', 'setBackendUrl')
    .addItem('View Current Backend', 'viewBackendUrl')
    .addToUi();
}

/**
 * Shows the Mosaico sidebar
 */
function showSidebar() {
  var html = HtmlService.createHtmlOutputFromFile('Sidebar')
    .setTitle('Mosaico AI')
    .setWidth(350);
  SpreadsheetApp.getUi().showSidebar(html);
}

/**
 * Shows about dialog
 */
function showAbout() {
  var ui = SpreadsheetApp.getUi();
  ui.alert(
    'Mosaico - AI Content Creation Co-Pilot',
    'Version 1.0.0\\n\\nYour AI assistant for content creation in Google Sheets.',
    ui.ButtonSet.OK
  );
}

/**
 * Gets the selected text from the active cell
 * @return {Object} Selected text and cell address
 */
function getSelectedText() {
  var sheet = SpreadsheetApp.getActiveSheet();
  var cell = sheet.getActiveCell();
  var text = cell.getValue().toString();
  var address = cell.getA1Notation();
  
  return {
    text: text,
    address: address,
    isEmpty: text.trim() === ''
  };
}

/**
 * Extracts an image URL from the selected cell, either from an =IMAGE() formula or raw text.
 * @return {Object} The extracted URL or an error.
 */
function getImageUrlFromSelectedCell() {
  try {
    var sheet = SpreadsheetApp.getActiveSheet();
    var cell = sheet.getActiveCell();
    var formula = cell.getFormula();
    var url = '';

    if (formula && formula.toUpperCase().indexOf('=IMAGE(') !== -1) {
      // Extract URL from =IMAGE("url") formula
      var matches = formula.match(/=IMAGE\("([^"]+)"/i);
      if (matches && matches.length > 1) {
        url = matches[1];
      }
    }
    
    // If no URL found in formula, fall back to the cell value
    if (!url) {
      url = cell.getValue().toString();
    }
    
    return {
      url: url.trim(),
      isEmpty: url.trim() === ''
    };
  } catch (e) {
    return {
      error: e.message
    };
  }
}

/**
 * Writes text to the active cell
 * @param {string} text - Text to write
 */
function writeToActiveCell(text) {
  var sheet = SpreadsheetApp.getActiveSheet();
  var cell = sheet.getActiveCell();
  cell.setValue(text);
}

/**
 * Writes array of variations to cells below the active cell
 * @param {Array<string>} variations - Array of text variations
 */
function writeVariationsToSheet(variations) {
  var sheet = SpreadsheetApp.getActiveSheet();
  var startCell = sheet.getActiveCell();
  var startRow = startCell.getRow();
  var col = startCell.getColumn();
  
  // Write each variation to a new row
  for (var i = 0; i < variations.length; i++) {
    sheet.getRange(startRow + i, col).setValue(variations[i]);
  }
  
  // Select the range of written variations
  sheet.setActiveRange(sheet.getRange(startRow, col, variations.length, 1));
}

/**
 * Calls the Mosaico backend API
 * @param {string} endpoint - API endpoint (e.g., '/api/v1/generate')
 * @param {Object} payload - Request payload
 * @return {Object} API response
 */
function callMosaicoAPI(endpoint, payload) {
  var properties = PropertiesService.getScriptProperties();
  var backendUrl = properties.getProperty('BACKEND_URL') || DEFAULT_BACKEND_URL;
  var url = backendUrl + endpoint;

  Logger.log('Attempting to call API. URL: ' + url);
  Logger.log('Payload: ' + JSON.stringify(payload));
  
  var options = {
    'method': 'post',
    'contentType': 'application/json',
    'payload': JSON.stringify(payload),
    'muteHttpExceptions': true
  };
  
  try {
    var response = UrlFetchApp.fetch(url, options);
    var responseCode = response.getResponseCode();
    var responseText = response.getContentText();

    Logger.log('API Response Code: ' + responseCode);
    
    if (responseCode !== 200) {
      Logger.log('API Error Response Text: ' + responseText);
      throw new Error('API Error: ' + responseText);
    }
    
    Logger.log('API Success. Response received.');
    return JSON.parse(responseText);
  } catch (error) {
    Logger.log('ERROR in callMosaicoAPI: ' + error.message);
    throw new Error('Failed to call Mosaico API: ' + error.message);
  }
}

/**
 * Generates text variations
 * Called from sidebar UI
 * 
 * @param {string} text - Original text
 * @param {number} count - Number of variations
 * @param {string} tone - Tone type (professional, casual, etc.)
 * @return {Object} API response with variations
 */
function generateVariations(prompt, count, contentType, tone, structure, imageUrl) {
  var backendUrl = getBackendUrl();
  if (!backendUrl) {
    return 'Backend URL not set. Please set it via the Mosaico AI > Settings menu.';
  }

  var url = backendUrl + '/api/v1/generate';
  var payload = {
    text: prompt,
    count: parseInt(count, 10),
    content_type: contentType,
    tone: tone,
    structure: structure,
    image_url: imageUrl,
  };

  try {
    var response = callMosaicoAPI('/api/v1/generate', payload);
    return {
      success: true,
      data: response
    };
  } catch (e) {
    return 'Error calling Mosaico API: ' + e.message;
  }
}

/**
 * Translates text
 * Called from sidebar UI
 * 
 * @param {string} text - Text to translate
 * @param {string} targetLanguage - Target language code
 * @return {Object} API response with translation
 */
function translateText(text, targetLanguage) {
  Logger.log('translateText function called. Text: "' + text + '", Target Language: ' + targetLanguage);
  var payload = {
    text: text,
    target_language: targetLanguage,
    maintain_tone: true,
    content_type: 'newsletter'
  };
  
  try {
    var response = callMosaicoAPI('/api/v1/translate', payload);
    Logger.log('translateText successful.');
    return {
      success: true,
      data: response
    };
  } catch (error) {
    Logger.log('ERROR in translateText: ' + error.message);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Refines text with one-click operations
 * Called from sidebar UI
 * 
 * @param {string} text - Text to refine
 * @param {string} operation - Operation type (shorten, fix_grammar, etc.)
 * @return {Object} API response with refined text
 */
function refineText(text, operation) {
  var backendUrl = getBackendUrl();
  if (!backendUrl) {
    return 'Backend URL not set. Please set it via the Mosaico AI > Settings menu.';
  }

  var url = backendUrl + '/api/v1/refine';
  var payload = {
    text: text,
    operation: operation,
    content_type: 'newsletter'
  };

  try {
    var response = callMosaicoAPI('/api/v1/refine', payload);
    return {
      success: true,
      data: response
    };
  } catch (e) {
    return 'Error calling Mosaico API: ' + e.message;
  }
}

/**
 * Generates text from an image URL and a prompt.
 * Called from sidebar UI
 */
function generateFromImage(imageUrl, text, count, tone, structure) {
  Logger.log('generateFromImage function called. Image URL: ' + imageUrl);
  var payload = {
    image_url: imageUrl,
    text: text,
    count: count,
    tone: tone,
    structure: structure, // This is now an array of objects
    content_type: 'newsletter' // Or make this dynamic if needed
  };

  try {
    // We can reuse the /generate-from-image endpoint which returns a similar structure
    var response = callMosaicoAPI('/api/v1/generate-from-image', payload);
    Logger.log('generateFromImage successful.');
    return {
      success: true,
      data: response
    };
  } catch (error) {
    Logger.log('ERROR in generateFromImage: ' + error.message);
    return {
      success: false,
      error: error.message
    };
  }
}

// --- CONFIGURATION FUNCTIONS ---

/**
 * Prompts the user to set the backend URL and stores it in script properties.
 */
function setBackendUrl() {
  var ui = SpreadsheetApp.getUi();
  var result = ui.prompt(
    'Set Backend URL',
    'Please enter the full URL of your Mosaico backend (e.g., https://your-url.run.app):',
    ui.ButtonSet.OK_CANCEL
  );

  if (result.getSelectedButton() == ui.Button.OK) {
    var backendUrl = result.getResponseText().trim();
    if (backendUrl) {
      PropertiesService.getScriptProperties().setProperty('BACKEND_URL', backendUrl);
      ui.alert('Backend URL has been set successfully.');
    } else {
      ui.alert('No URL entered. The backend URL has not been changed.');
    }
  }
}

/**
 * Displays the currently configured backend URL to the user.
 */
function viewBackendUrl() {
  var backendUrl = PropertiesService.getScriptProperties().getProperty('BACKEND_URL');
  var ui = SpreadsheetApp.getUi();
  if (backendUrl) {
    ui.alert('Current Backend URL', 'The current backend URL is: ' + backendUrl, ui.ButtonSet.OK);
  } else {
    ui.alert(
      'Backend URL Not Set',
      'The backend URL has not been set yet. Please set it via the Mosaico AI > Settings menu.',
      ui.ButtonSet.OK
    );
  }
}

/**
 * Retrieves the backend URL from script properties.
 * @returns {string|null} The stored backend URL or null if not set.
 */
function getBackendUrl() {
  return PropertiesService.getScriptProperties().getProperty('BACKEND_URL');
}

/**
 * Logs the details of an API request for debugging purposes.
 * @param {string} url The URL being called.
 * @param {Object} payload The JSON payload sent in the request.
 * @param {Object} options The options used for the UrlFetchApp call.
 */
function logApiRequest(url, payload, options) {
  Logger.log(
    JSON.stringify(
      {
        message: 'Mosaico API Request',
        url: url,
        payload: payload,
        options: options,
      },
      null,
      2
    )
  );
}

/**
 * Logs the details of an API response for debugging purposes.
 * @param {number} responseCode The HTTP status code of the response.
 * @param {string} responseBody The body of the response.
 */
function logApiResponse(responseCode, responseBody) {
  var logEntry = {
    message: 'Mosaico API Response',
    responseCode: responseCode,
  };

  try {
    // Try to parse the body as JSON for prettier logging
    logEntry.responseBody = JSON.parse(responseBody);
  } catch (e) {
    // If it's not JSON, log it as raw text
    logEntry.responseBody = responseBody;
  }

  Logger.log(JSON.stringify(logEntry, null, 2));
}
