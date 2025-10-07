/**
 * Mosaico Google Sheets Add-on
 * AI Content Creation Co-Pilot
 * 
 * This add-on connects to the Mosaico FastAPI backend
 * to provide AI-powered content generation directly in Sheets
 */

// Backend API Configuration
// TODO: Replace with your Cloud Run URL
const BACKEND_URL = 'https://mosaico-backend-YOUR-PROJECT.run.app';

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
function onOpen(e) {
  const ui = SpreadsheetApp.getUi();
  ui.createAddonMenu()
    .addItem('Open Mosaico', 'showSidebar')
    .addSeparator()
    .addItem('About', 'showAbout')
    .addToUi();
}

/**
 * Shows the Mosaico sidebar
 */
function showSidebar() {
  const html = HtmlService.createHtmlOutputFromFile('Sidebar')
    .setTitle('Mosaico AI')
    .setWidth(350);
  SpreadsheetApp.getUi().showSidebar(html);
}

/**
 * Shows about dialog
 */
function showAbout() {
  const ui = SpreadsheetApp.getUi();
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
  const sheet = SpreadsheetApp.getActiveSheet();
  const cell = sheet.getActiveCell();
  const text = cell.getValue().toString();
  const address = cell.getA1Notation();
  
  return {
    text: text,
    address: address,
    isEmpty: text.trim() === ''
  };
}

/**
 * Writes text to the active cell
 * @param {string} text - Text to write
 */
function writeToActiveCell(text) {
  const sheet = SpreadsheetApp.getActiveSheet();
  const cell = sheet.getActiveCell();
  cell.setValue(text);
}

/**
 * Writes array of variations to cells below the active cell
 * @param {Array<string>} variations - Array of text variations
 */
function writeVariationsToSheet(variations) {
  const sheet = SpreadsheetApp.getActiveSheet();
  const startCell = sheet.getActiveCell();
  const startRow = startCell.getRow();
  const col = startCell.getColumn();
  
  // Write each variation to a new row
  for (let i = 0; i < variations.length; i++) {
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
  const url = BACKEND_URL + endpoint;
  
  const options = {
    'method': 'post',
    'contentType': 'application/json',
    'payload': JSON.stringify(payload),
    'muteHttpExceptions': true
  };
  
  try {
    const response = UrlFetchApp.fetch(url, options);
    const responseCode = response.getResponseCode();
    const responseText = response.getContentText();
    
    if (responseCode !== 200) {
      throw new Error('API Error: ' + responseText);
    }
    
    return JSON.parse(responseText);
  } catch (error) {
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
function generateVariations(text, count, tone) {
  const payload = {
    text: text,
    count: count,
    tone: tone || 'professional',
    content_type: 'newsletter'
  };
  
  try {
    const response = callMosaicoAPI('/api/v1/generate', payload);
    return {
      success: true,
      data: response
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
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
  const payload = {
    text: text,
    target_language: targetLanguage,
    maintain_tone: true,
    content_type: 'newsletter'
  };
  
  try {
    const response = callMosaicoAPI('/api/v1/translate', payload);
    return {
      success: true,
      data: response
    };
  } catch (error) {
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
  const payload = {
    text: text,
    operation: operation,
    content_type: 'newsletter'
  };
  
  try {
    const response = callMosaicoAPI('/api/v1/refine', payload);
    return {
      success: true,
      data: response
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}
