# SRM Result Analysis Dashboard (Consolidated)

A professional, mobile-friendly faculty portal for consolidated student result analysis at SRM Institute of Science and Technology. This system is designed for **Faculty Advisors (FA)** to upload a single section-wide consolidated Excel file and generate a final analysis report.

## Features

- **Faculty Authentication** - Secure institutional login for SRM faculty
- **Consolidated Section Workflow** - Single-file upload process for all subjects in a section
- **FA-Only Access** - Designed for Faculty Advisors to manage their assigned sections
- **Smart Form Validation** - Dropdowns for Year, Semester, Department, and Section (A-Z)
- **Drag-and-Drop Upload** - Secure upload for consolidated .xlsx or .xls files
- **Formatted Report Preview** - Backend-returned data analysis with subject-wise performance
- **Official Branding** - Institutional color scheme (#3078b8) and logo
- **Print-Ready Reports** - A4 layout with signature lines for FA and HOD
- **Responsive Design** - Mobile-first UI for all university stakeholders

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Styling**: Tailwind CSS v4 with custom SRM theme
- **UI Components**: shadcn/ui
- **Backend Mock**: Modular API architecture (lib/mockApi.js and lib/auth.js)

## Core Workflow

1. **Login**: Faculty logs in with their SRM credentials.
2. **Details**: FA enters Section details (Year, Semester, Dept, Section A-Z, FA Name).
3. **Upload**: FA uploads **one consolidated Excel file** containing all subject marks.
4. **Preview**: FA previews the formatted report returned by the backend.
5. **Finalize**: FA prints or downloads the A4-formatted consolidated report.

## Mock API Integration (`lib/mockApi.js`)

The system uses a modular mock API layer designed to be replaced with a real backend (e.g., Firebase, Node.js) effortlessly:

- `uploadSectionExcel(details, file)`: Simulates file upload and validation.
- `getFormattedReport(details)`: Simulates backend parsing and returns report JSON.
- `getSectionUploadStatus(details)`: Checks if a section already has an uploaded report.

## Report Layout (A4 Print-Friendly)

The Final Report includes:
- **SRM Header**: Logo and institutional title.
- **Section Metadata**: Department, Year/Semester, Section, and Faculty Advisor Name.
- **Summary Metrics**: Total Students, Overall Pass %, and Average CGPA.
- **Analysis Table**: Subject-wise student counts (Appeared/Passed/Failed) and Average CGPA.
- **Signatures**: Official signature lines for the Faculty Advisor and Head of Department.

---
**Built for SRM Institute of Science and Technology**  
*Learn • Leap • Lead*
