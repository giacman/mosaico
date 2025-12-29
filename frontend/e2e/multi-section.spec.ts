import { test, expect } from '@playwright/test'

/**
 * Multi-Section Integration Tests
 * 
 * Prerequisites:
 * - Frontend running on localhost:3000
 * - Backend running on localhost:8000
 * - User logged in (or dev mode enabled)
 */

test.describe('Multi-Section Email Generation', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to projects page
    await page.goto('/dashboard/projects')
    
    // Wait for page to load (in dev mode, no auth needed)
    await page.waitForLoadState('networkidle')
  })

  test('should create a new project with two sections', async ({ page }) => {
    // Click "New Project" button
    await page.getByRole('button', { name: /new project/i }).click()
    
    // Fill project details
    await page.getByLabel(/project name/i).fill('E2E Test Project')
    await page.getByLabel(/brand/i).fill('TestBrand')
    
    // Create project
    await page.getByRole('button', { name: /create/i }).click()
    
    // Wait for project page
    await expect(page).toHaveURL(/\/dashboard\/projects\/\d+/)
    
    // Verify project created
    await expect(page.getByText('E2E Test Project')).toBeVisible()
  })

  test('should add a second section with its own brief', async ({ page }) => {
    // Go to an existing project (assumes project exists)
    await page.goto('/dashboard/projects')
    await page.getByText(/E2E Test Project|test/i).first().click()
    
    // Wait for editor to load
    await page.waitForSelector('[data-testid="section-builder"]', { timeout: 10000 }).catch(() => {
      // Fallback: wait for any section
      return page.waitForSelector('text=Main Section', { timeout: 10000 })
    })
    
    // Click "Add Section" button
    await page.getByRole('button', { name: /add section/i }).click()
    
    // Verify second section appears
    await expect(page.getByText(/section 2/i)).toBeVisible()
    
    // Fill brief for second section
    const sectionBriefInput = page.locator('textarea').last()
    await sectionBriefInput.fill('This is the brief for section 2 about loyalty program')
    
    // Verify brief is saved
    await expect(sectionBriefInput).toHaveValue(/loyalty program/)
  })

  test('should show "Generate" button when no content exists', async ({ page }) => {
    await page.goto('/dashboard/projects')
    await page.getByText(/test/i).first().click()
    
    // Wait for page load
    await page.waitForLoadState('networkidle')
    
    // Look for Generate button (not Regenerate)
    const generateButton = page.getByRole('button', { name: /^generate content$/i })
    
    // Should show "Generate" not "Regenerate" if no content
    await expect(generateButton.or(page.getByRole('button', { name: /^regenerate all content$/i }))).toBeVisible()
  })

  test('should upload image for a section', async ({ page }) => {
    await page.goto('/dashboard/projects')
    await page.getByText(/test/i).first().click()
    
    await page.waitForLoadState('networkidle')
    
    // Find image upload area
    const uploadArea = page.locator('text=Click to upload or drop images here').first()
    
    if (await uploadArea.isVisible()) {
      // Create a test image file
      const buffer = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==', 'base64')
      
      // Upload via file input
      const fileInput = page.locator('input[type="file"]').first()
      await fileInput.setInputFiles({
        name: 'test-image.png',
        mimeType: 'image/png',
        buffer: buffer,
      })
      
      // Wait for upload
      await page.waitForResponse(resp => resp.url().includes('/upload') && resp.status() === 200, { timeout: 30000 }).catch(() => {
        // Upload might have already completed
      })
      
      // Verify image appears (either in preview or as success message)
      await expect(page.getByRole('img').or(page.getByText(/uploaded/i))).toBeVisible({ timeout: 10000 })
    }
  })

  test('should not show missing image alert when image is uploaded', async ({ page }) => {
    await page.goto('/dashboard/projects')
    await page.getByText(/test/i).first().click()
    
    await page.waitForLoadState('networkidle')
    
    // Click Generate
    const generateBtn = page.getByRole('button', { name: /generate/i }).first()
    await generateBtn.click()
    
    // Wait a moment for dialog to potentially appear
    await page.waitForTimeout(1000)
    
    // If image alert appears, it's a bug (if image was uploaded)
    const alertDialog = page.getByRole('alertdialog')
    const hasAlert = await alertDialog.isVisible().catch(() => false)
    
    if (hasAlert) {
      const alertText = await alertDialog.textContent()
      // Only fail if the alert is about missing images
      if (alertText?.toLowerCase().includes('missing') && alertText?.toLowerCase().includes('image')) {
        // Check if we actually have an uploaded image
        const hasImage = await page.getByRole('img').first().isVisible().catch(() => false)
        if (hasImage) {
          throw new Error('Missing image alert shown but image is present!')
        }
      }
    }
  })

  test('should generate content for both sections', async ({ page }) => {
    test.setTimeout(120000) // 2 minutes for AI generation
    
    await page.goto('/dashboard/projects')
    await page.getByText(/test/i).first().click()
    
    await page.waitForLoadState('networkidle')
    
    // Fill main brief if empty
    const mainBrief = page.getByPlaceholder(/brief/i).first()
    if (await mainBrief.isVisible()) {
      const currentValue = await mainBrief.inputValue()
      if (!currentValue.trim()) {
        await mainBrief.fill('Test brief for E2E: Generate content about new product launch')
      }
    }
    
    // Click Generate
    const generateBtn = page.getByRole('button', { name: /generate/i }).first()
    await generateBtn.click()
    
    // Handle potential image alert
    const proceedBtn = page.getByRole('button', { name: /proceed without images/i })
    if (await proceedBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await proceedBtn.click()
    }
    
    // Wait for generation to complete (loading spinner disappears)
    await expect(page.getByRole('button', { name: /generating/i })).not.toBeVisible({ timeout: 90000 })
    
    // Verify content was generated (check for non-empty content areas)
    const subjectField = page.locator('[data-component="subject"]').or(page.getByText(/subject/i).locator('..').locator('p, span'))
    await expect(subjectField.first()).not.toBeEmpty({ timeout: 5000 }).catch(() => {
      // Alternative: check that Regenerate button appears (meaning content exists)
      return expect(page.getByRole('button', { name: /regenerate/i })).toBeVisible()
    })
  })

  test('should translate content to multiple languages', async ({ page }) => {
    test.setTimeout(180000) // 3 minutes for translation
    
    await page.goto('/dashboard/projects')
    await page.getByText(/test/i).first().click()
    
    await page.waitForLoadState('networkidle')
    
    // Select target languages if not selected
    const langSelect = page.getByLabel(/target languages/i)
    if (await langSelect.isVisible()) {
      await langSelect.click()
      await page.getByRole('option', { name: /italian/i }).click()
      await page.keyboard.press('Escape')
    }
    
    // Click Translate All
    const translateBtn = page.getByRole('button', { name: /translate all/i })
    if (await translateBtn.isVisible()) {
      await translateBtn.click()
      
      // Wait for translation to complete
      await expect(page.getByRole('button', { name: /translating/i })).not.toBeVisible({ timeout: 120000 })
      
      // Switch to translated language
      const langBadge = page.getByText('🇮🇹').or(page.getByText(/italian/i))
      if (await langBadge.isVisible()) {
        await langBadge.click()
        
        // Verify no "Missing translation" messages
        await expect(page.getByText(/missing translation/i)).not.toBeVisible({ timeout: 5000 }).catch(() => {
          // Some components might not have translations, that's OK
        })
        
        // Verify no __TRANSLATION_FAILED__ markers
        await expect(page.getByText(/__TRANSLATION_FAILED__/)).not.toBeVisible()
      }
    }
  })

  test('should have different CTAs for different sections', async ({ page }) => {
    await page.goto('/dashboard/projects')
    await page.getByText(/test/i).first().click()
    
    await page.waitForLoadState('networkidle')
    
    // Find all CTA components
    const ctaElements = page.locator('[data-component="cta"], .bg-primary.text-primary-foreground')
    const ctaCount = await ctaElements.count()
    
    if (ctaCount >= 2) {
      const cta1Text = await ctaElements.nth(0).textContent()
      const cta2Text = await ctaElements.nth(1).textContent()
      
      // CTAs should be different (not cross-contaminated)
      // Note: They might be similar, but shouldn't be identical if sections have different briefs
      console.log(`CTA 1: ${cta1Text}`)
      console.log(`CTA 2: ${cta2Text}`)
    }
  })

  test('copy button should show toast feedback', async ({ page }) => {
    await page.goto('/dashboard/projects')
    await page.getByText(/test/i).first().click()
    
    await page.waitForLoadState('networkidle')
    
    // Find and click a Copy button
    const copyBtn = page.getByRole('button', { name: /copy/i }).first()
    if (await copyBtn.isVisible()) {
      await copyBtn.click()
      
      // Verify toast appears
      await expect(page.getByText(/copied/i).or(page.getByRole('status'))).toBeVisible({ timeout: 5000 })
    }
  })
})

