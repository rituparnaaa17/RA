// Mock API module for section-level consolidated Excel upload
// This file can be easily replaced with Firebase or real backend

const sectionsStore = []
let changeListeners = []

// Upload consolidated section Excel (single file per section)
export async function uploadSectionExcel(sectionDetails, file) {
  // Simulate file upload with delay
  await delay(1500)

  // Simulate validation errors (5% chance)
  if (Math.random() < 0.05) {
    return {
      success: false,
      message: "Excel validation failed",
      errors: [
        "Sheet 'CS101': Missing required column 'Student Name'",
        "Sheet 'CS102': Invalid marks format in row 8",
        "Sheet 'MA101': CGPA out of range in row 15",
      ],
    }
  }

  // Store the section data
  const sectionKey = `${sectionDetails.year}-${sectionDetails.semester}-${sectionDetails.department}-${sectionDetails.section}`

  const existingIndex = sectionsStore.findIndex((s) => s.key === sectionKey)

  const sectionData = {
    key: sectionKey,
    ...sectionDetails,
    fileName: file.name,
    uploadedAt: new Date().toISOString(),
    uploaded: true,
  }

  if (existingIndex >= 0) {
    sectionsStore[existingIndex] = sectionData
  } else {
    sectionsStore.push(sectionData)
  }

  notifyListeners()

  return {
    success: true,
    message: "Section Excel uploaded successfully",
  }
}

// Get formatted report data (backend would parse Excel and return this)
export async function getFormattedReport(sectionDetails) {
  await delay(1000)

  const sectionKey = `${sectionDetails.year}-${sectionDetails.semester}-${sectionDetails.department}-${sectionDetails.section}`
  const section = sectionsStore.find((s) => s.key === sectionKey)

  if (!section) {
    throw new Error("No data found for this section")
  }

  // Simulate backend returning formatted data
  const subjects = generateMockSubjects(6)
  const students = generateMockStudents(45)

  return {
    sectionDetails: {
      year: sectionDetails.year,
      semester: sectionDetails.semester,
      department: sectionDetails.department,
      section: sectionDetails.section,
      facultyAdvisor: sectionDetails.facultyAdvisor,
    },
    subjects,
    students,
    summary: {
      totalStudents: students.length,
      totalSubjects: subjects.length,
      overallPassPercentage: calculateOverallPass(students, subjects),
      averageCGPA: calculateAverageCGPA(students),
    },
    uploadedAt: section.uploadedAt,
    fileName: section.fileName,
  }
}

// Check if section has uploaded file
export function getSectionUploadStatus(sectionDetails) {
  const sectionKey = `${sectionDetails.year}-${sectionDetails.semester}-${sectionDetails.department}-${sectionDetails.section}`
  const section = sectionsStore.find((s) => s.key === sectionKey)
  return section || null
}

// Subscribe to changes
export function subscribeToChanges(callback) {
  changeListeners.push(callback)
  return () => {
    changeListeners = changeListeners.filter((cb) => cb !== callback)
  }
}

function notifyListeners() {
  changeListeners.forEach((cb) => cb())
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

// Mock data generators
function generateMockSubjects(count) {
  const subjectCodes = ["CS101", "CS102", "MA101", "PH101", "CH101", "EE101", "ME101", "EC101"]
  const subjectNames = [
    "Programming in C",
    "Data Structures",
    "Engineering Mathematics",
    "Physics",
    "Chemistry",
    "Electrical Circuits",
    "Engineering Mechanics",
    "Digital Electronics",
  ]

  return Array.from({ length: count }, (_, i) => {
    const totalStudents = 45
    const appeared = totalStudents - Math.floor(Math.random() * 3)
    const failed = Math.floor(Math.random() * 8)
    const passed = appeared - failed

    return {
      subjectCode: subjectCodes[i % subjectCodes.length],
      subjectName: subjectNames[i % subjectNames.length],
      totalStudents,
      studentsAppeared: appeared,
      studentsPassed: passed,
      studentsFailed: failed,
      passPercentage: Math.round((passed / appeared) * 100 * 10) / 10,
      averageCGPA: (Math.random() * 2 + 7).toFixed(2),
    }
  })
}

function generateMockStudents(count) {
  const firstNames = ["Aarav", "Ananya", "Arjun", "Diya", "Ishaan", "Kavya", "Rohan", "Saanvi", "Vihaan", "Anvi"]
  const lastNames = ["Kumar", "Singh", "Patel", "Sharma", "Reddy", "Nair", "Verma", "Gupta", "Mehta", "Joshi"]

  return Array.from({ length: count }, (_, i) => {
    const cgpa = (Math.random() * 3 + 6).toFixed(2)

    return {
      rollNo: `RA2111003010${String(i + 1).padStart(3, "0")}`,
      studentName: `${firstNames[i % firstNames.length]} ${lastNames[Math.floor(i / firstNames.length) % lastNames.length]}`,
      cgpa: Number.parseFloat(cgpa),
      result: Number.parseFloat(cgpa) >= 5.0 ? "Pass" : "Fail",
    }
  })
}

function calculateOverallPass(students, subjects) {
  const passed = students.filter((s) => s.result === "Pass").length
  return Math.round((passed / students.length) * 100 * 10) / 10
}

function calculateAverageCGPA(students) {
  const sum = students.reduce((acc, s) => acc + s.cgpa, 0)
  return (sum / students.length).toFixed(2)
}
