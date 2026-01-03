// Mock API module with stateful in-memory management

export interface Subject {
  id: string
  subjectCode: string
  subjectName: string
  section: string
  facultyEmail: string
  year: string
  semester: string
  department: string
  uploaded: boolean
  fileName?: string
  uploadedAt?: string
}

export interface StudentResult {
  rollNo: string
  studentName: string
  marks: number
  percentage: number
  result: "Pass" | "Fail"
}

export interface FinalReportData {
  totalStudents: number
  passed: number
  failed: number
  average: number
  students: Array<StudentResult & { [key: string]: number | string }>
}

let subjectsStore: Subject[] = [
  {
    id: "seed-1",
    subjectCode: "CS101",
    subjectName: "Data Structures",
    section: "A",
    facultyEmail: "rajesh.kumar@srmist.edu.in",
    year: "2nd",
    semester: "3",
    department: "CSE",
    uploaded: true,
    fileName: "CS101_results.xlsx",
    uploadedAt: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: "seed-2",
    subjectCode: "CS102",
    subjectName: "Algorithms",
    section: "A",
    facultyEmail: "priya.sharma@srmist.edu.in",
    year: "2nd",
    semester: "3",
    department: "CSE",
    uploaded: true,
    fileName: "CS102_results.xlsx",
    uploadedAt: new Date(Date.now() - 43200000).toISOString(),
  },
]

let changeListeners: Array<() => void> = []

export async function login(email: string, password: string): Promise<{ success: boolean; message?: string }> {
  await delay(500)

  if (!email.includes("srmist.edu.in") && !email.includes("srmuniv")) {
    return { success: false, message: "Only SRM faculty email IDs are allowed" }
  }

  return { success: true }
}

export async function fetchSemesterSubjects(params: {
  year: string
  semester: string
  department: string
  section: string
}): Promise<Subject[]> {
  await delay(300)

  return subjectsStore.filter(
    (s) =>
      s.year === params.year &&
      s.semester === params.semester &&
      s.department === params.department &&
      s.section === params.section,
  )
}

export async function addSubject(params: {
  year: string
  semester: string
  department: string
  section: string
  subjectName: string
  subjectCode: string
  facultyEmail: string
}): Promise<Subject> {
  await delay(400)

  const newSubject: Subject = {
    id: `subject-${Date.now()}-${Math.random()}`,
    subjectCode: params.subjectCode,
    subjectName: params.subjectName,
    section: params.section,
    facultyEmail: params.facultyEmail,
    year: params.year,
    semester: params.semester,
    department: params.department,
    uploaded: false,
  }

  subjectsStore.push(newSubject)
  notifyListeners()

  return newSubject
}

export async function uploadSubjectFile(
  subjectId: string,
  file: File,
  onProgress?: (progress: number) => void,
): Promise<{ success: boolean; message: string; errors?: string[] }> {
  // Simulate upload progress
  for (let i = 0; i <= 100; i += 10) {
    await delay(100)
    onProgress?.(i)
  }

  // Simulate validation errors (5% chance)
  if (Math.random() < 0.05) {
    return {
      success: false,
      message: "Validation failed",
      errors: ["Row 5: Missing student name", "Row 12: Invalid marks value", "Row 18: Roll number format incorrect"],
    }
  }

  // Update subject with upload info
  subjectsStore = subjectsStore.map((s) =>
    s.id === subjectId
      ? {
          ...s,
          uploaded: true,
          fileName: file.name,
          uploadedAt: new Date().toISOString(),
        }
      : s,
  )

  notifyListeners()

  return {
    success: true,
    message: "File uploaded successfully",
  }
}

export async function previewSubject(subjectId: string): Promise<StudentResult[]> {
  await delay(600)

  const subject = subjectsStore.find((s) => s.id === subjectId)
  if (!subject) throw new Error("Subject not found")

  // Generate mock student data
  return generateMockStudentData(30)
}

export async function generateFinalReport(params: {
  year: string
  semester: string
  department: string
  section: string
}): Promise<FinalReportData> {
  await delay(2000)

  const subjects = await fetchSemesterSubjects(params)
  const uploadedSubjects = subjects.filter((s) => s.uploaded)

  if (uploadedSubjects.length < 4) {
    throw new Error("Minimum 4 subjects required to generate final report")
  }

  // Generate merged student data
  const students = generateMockStudentData(50)
  const totalStudents = students.length
  const passed = students.filter((s) => s.result === "Pass").length
  const failed = totalStudents - passed
  const average = students.reduce((sum, s) => sum + s.percentage, 0) / totalStudents

  return {
    totalStudents,
    passed,
    failed,
    average: Math.round(average * 10) / 10,
    students: students.map((s) => ({
      ...s,
      ...uploadedSubjects.reduce(
        (acc, subj, idx) => {
          acc[subj.subjectCode] = Math.floor(Math.random() * 40) + 60
          return acc
        },
        {} as Record<string, number>,
      ),
    })),
  }
}

export function subscribeToChanges(callback: () => void): () => void {
  changeListeners.push(callback)
  return () => {
    changeListeners = changeListeners.filter((cb) => cb !== callback)
  }
}

function notifyListeners() {
  changeListeners.forEach((cb) => cb())
}

// Helper function to simulate network delay
function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

// Generate mock student data
function generateMockStudentData(count: number): StudentResult[] {
  const firstNames = [
    "Aarav",
    "Ananya",
    "Arjun",
    "Diya",
    "Ishaan",
    "Kavya",
    "Rohan",
    "Saanvi",
    "Vihaan",
    "Anvi",
    "Aditya",
    "Sara",
    "Ayaan",
    "Aadhya",
    "Krishna",
    "Myra",
  ]
  const lastNames = [
    "Kumar",
    "Singh",
    "Patel",
    "Sharma",
    "Reddy",
    "Nair",
    "Verma",
    "Gupta",
    "Mehta",
    "Joshi",
    "Iyer",
    "Menon",
    "Rao",
    "Das",
    "Pillai",
    "Bose",
  ]

  return Array.from({ length: count }, (_, i) => {
    const marks = Math.floor(Math.random() * 60) + 40
    const percentage = marks
    return {
      rollNo: `RA2111003010${String(i + 1).padStart(3, "0")}`,
      studentName: `${firstNames[i % firstNames.length]} ${lastNames[Math.floor(i / firstNames.length) % lastNames.length]}`,
      marks,
      percentage,
      result: marks >= 50 ? "Pass" : "Fail",
    }
  })
}

export const EXCEL_TEMPLATE_COLUMNS = [
  "Roll Number",
  "Student Name",
  "Marks (out of 100)",
  "Percentage",
  "Result (Pass/Fail)",
]

export const SAMPLE_TEMPLATE_FILENAME = "SRM_Result_Template.xlsx"
