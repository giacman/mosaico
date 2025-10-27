"use server"

function isValidEmail(email: string): boolean {
  // Simple RFC 5322-compatible check
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

export async function requestAccess(prevState: any, formData: FormData) {
  const name = String(formData.get("name") || "").trim()
  const email = String(formData.get("email") || "").trim()
  const note = String(formData.get("note") || "").trim()

  if (name.length < 2 || name.length > 120) {
    return { ok: false, error: "Name must be 2-120 characters" }
  }
  if (!isValidEmail(email) || email.length > 200) {
    return { ok: false, error: "Provide a valid email" }
  }
  if (note.length > 1000) {
    return { ok: false, error: "Note is too long" }
  }

  const webhook = process.env.SLACK_WEBHOOK_URL
  const body = {
    text: `🔐 Access request\nName: ${name}\nEmail: ${email}\nNote: ${note || "-"}`
  }

  try {
    if (webhook) {
      await fetch(webhook, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      })
    } else {
      console.log("Access request:", body)
    }
    return { ok: true }
  } catch {
    return { ok: false, error: "Failed to send request" }
  }
}


