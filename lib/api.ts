
const API_BASE_URL = "http://localhost:8000/api"

export interface SectionDetails {
  year: string
  semester: string
  department: string
  section: string
  facultyAdvisor: string
  batch?: string
  examDate?: string
}

/**
 * Uploads an Excel file with section details.
 * The backend processes it, renders report_landscape.html and returns it.
 *
 * On success: { success: true, reportHtml: "<html>..." }
 * On failure: { success: false, message: "...", errors: [...] }
 */
export async function uploadSectionExcel(
  details: SectionDetails,
  file: File
): Promise<{ success: boolean; message: string; reportHtml?: string; errors?: string[] }> {
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
      body: formData,
    })

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
      message: error.message || "Failed to connect to backend. Is the server running on port 8000?",
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
