
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

export interface SectionDetails {
  year: string
  semester: string
  department: string
  section: string
  facultyAdvisor: string
  batch?: string
  examDate?: string
}

// ── Token helpers ──────────────────────────────────────────────────────────────
export function saveToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("ra_token", token)
  }
}

export function getToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("ra_token")
  }
  return null
}

export function clearToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("ra_token")
    localStorage.removeItem("ra_user")
  }
}

// ── Upload ─────────────────────────────────────────────────────────────────────
/**
 * Uploads an Excel file with section details.
 * Requires a valid JWT token stored from login.
 *
 * On success: { success: true, reportHtml: "<html>..." }
 * On failure: { success: false, message: "...", errors: [...] }
 */
export async function uploadSectionExcel(
  details: SectionDetails,
  file: File
): Promise<{ success: boolean; message: string; reportHtml?: string; errors?: string[] }> {
  const token = getToken()
  if (!token) {
    return {
      success: false,
      message: "You are not logged in. Please log in again.",
      errors: ["No auth token found"],
    }
  }

  const formData = new FormData()
  formData.append("file", file)
  formData.append("dept", details.department)
  formData.append("year", details.year)
  formData.append("sem", details.semester)
  formData.append("section", details.section)
  formData.append("faculty_advisor_name", details.facultyAdvisor)
  formData.append("batch", details.batch ?? "")
  formData.append("exam_date", details.examDate ?? "")

  try {
    const res = await fetch(`${API_BASE_URL}/reports/upload`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    })

    if (res.status === 401) {
      clearToken()
      return {
        success: false,
        message: "Session expired. Please log in again.",
        errors: ["Token expired"],
      }
    }

    const htmlText = await res.text()

    if (!res.ok) {
      const stripped = htmlText.replace(/<[^>]+>/g, "").trim()
      return {
        success: false,
        message: stripped || `Server error (${res.status})`,
        errors: [stripped],
      }
    }

    return {
      success: true,
      message: "Report generated successfully",
      reportHtml: htmlText,
    }
  } catch (error: any) {
    return {
      success: false,
      message: error.message || "Failed to connect to backend.",
      errors: [error.message],
    }
  }
}

/**
 * Opens the HTML report string in a new browser tab.
 */
export function openReportInNewTab(htmlContent: string): void {
  const blob = new Blob([htmlContent], { type: "text/html" })
  const url = URL.createObjectURL(blob)
  window.open(url, "_blank")
  setTimeout(() => URL.revokeObjectURL(url), 10000)
}
