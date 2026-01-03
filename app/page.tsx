"use client"

import { useState } from "react"
import { LoginPage } from "@/components/login-page"
import { Dashboard } from "@/components/dashboard"
import { FinalReportPage } from "@/components/final-report-page"

type Page = "login" | "dashboard" | "report"

export default function Home() {
  const [currentPage, setCurrentPage] = useState<Page>("login")
  const [facultyEmail, setFacultyEmail] = useState("")
  const [reportData, setReportData] = useState<any>(null)

  const handleLogin = (email: string) => {
    setFacultyEmail(email)
    setCurrentPage("dashboard")
  }

  const handleViewReport = (data: any) => {
    setReportData(data)
    setCurrentPage("report")
  }

  const handleBackToDashboard = () => {
    setCurrentPage("dashboard")
  }

  return (
    <>
      {currentPage === "login" && <LoginPage onLogin={handleLogin} />}
      {currentPage === "dashboard" && <Dashboard facultyEmail={facultyEmail} onViewReport={handleViewReport} />}
      {currentPage === "report" && <FinalReportPage reportData={reportData} onBack={handleBackToDashboard} />}
    </>
  )
}
