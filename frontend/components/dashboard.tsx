"use client"

import type React from "react"

import { useState } from "react"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Upload, FileCheck, AlertCircle, CheckCircle2, LogOut } from "lucide-react"
import * as api from "@/lib/api"
import { useToast } from "@/hooks/use-toast"
import { DeveloperPortal } from "@/components/developer-section"

interface DashboardProps {
  facultyEmail: string
  onViewReport?: (reportData: any) => void
  onLogout?: () => void
}

export function Dashboard({ facultyEmail, onViewReport, onLogout }: DashboardProps) {
  // Semester mapping based on year
  const yearToSemesters: Record<string, number[]> = {
    "1st": [1, 2],
    "2nd": [3, 4],
    "3rd": [5, 6],
    "4th": [7, 8],
  }

  // Section details form state
  const [year, setYear] = useState("")
  const [semester, setSemester] = useState("")
  const [department, setDepartment] = useState("")
  const [section, setSection] = useState("")
  const [facultyAdvisor, setFacultyAdvisor] = useState("")
  const [batch, setBatch] = useState("")
  const [examDate, setExamDate] = useState("")

  // Upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<any>(null)
  const [reportHtml, setReportHtml] = useState<string | null>(null)
  const [uploadErrors, setUploadErrors] = useState<string[]>([])
  const [isDragging, setIsDragging] = useState(false)

  const { toast } = useToast()

  // Check if form is complete
  const isFormComplete = year && semester && department && section && facultyAdvisor

  const handleFileSelect = (file: File) => {
    const validTypes = ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"]

    if (!validTypes.includes(file.type)) {
      toast({
        title: "Invalid File Type",
        description: "Please upload an Excel file (.xlsx or .xls)",
        variant: "destructive",
      })
      return
    }

    setSelectedFile(file)
    setUploadErrors([])
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const file = e.dataTransfer.files[0]
    if (file) handleFileSelect(file)
  }

  const handleUpload = async () => {
    if (!selectedFile || !isFormComplete) return

    setIsUploading(true)
    setUploadErrors([])
    setReportHtml(null)

    try {
      const result = await api.uploadSectionExcel(
        { year, semester, department, section, facultyAdvisor, batch, examDate },
        selectedFile,
      )

      if (result.success && result.reportHtml) {
        setReportHtml(result.reportHtml)
        toast({
          title: "Report Generated",
          description: "Excel processed successfully. Click 'Preview Report' to open it.",
        })

        setUploadStatus({
          fileName: selectedFile.name,
          uploadedAt: new Date().toISOString(),
        })
        setSelectedFile(null)
      } else {
        setUploadErrors(result.errors || [result.message])
        toast({
          title: "Upload Failed",
          description: result.message,
          variant: "destructive",
        })
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to upload file",
        variant: "destructive",
      })
    } finally {
      setIsUploading(false)
    }
  }

  const handlePreviewReport = () => {
    if (!reportHtml) return
    api.openReportInNewTab(reportHtml)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/5 via-background to-primary/10">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between max-w-6xl md:px-8">
          <div className="flex items-center gap-3">
            <DeveloperPortal />
            <Image src="/srm-logo.png" alt="SRM Logo" width={48} height={48} className="h-12 w-12" />
            <div>
              <h1 className="text-lg font-bold text-primary md:text-xl">SRM Result Analysis</h1>
              <p className="text-xs text-muted-foreground">Faculty Dashboard</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden md:block text-right">
              <p className="text-sm font-medium">{facultyAdvisor || "Faculty"}</p>
              <p className="text-xs text-muted-foreground">{facultyEmail}</p>
            </div>
            <Button variant="outline" size="sm" onClick={onLogout}>
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6 md:py-8 max-w-6xl md:px-8">
        <div className="space-y-6">
          {/* Page Title */}
          <div>
            <h2 className="text-2xl font-bold text-primary md:text-3xl">Section Details</h2>
            <p className="text-sm text-muted-foreground">
              Enter section information and upload consolidated Excel file
            </p>
          </div>

          {/* Section Details Form */}
          <Card>
            <CardHeader>
              <CardTitle>Section Information</CardTitle>
              <CardDescription>Fill in all required details for your section</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                {/* Year */}
                <div className="space-y-2">
                  <Label htmlFor="year">Year *</Label>
                  <Select value={year} onValueChange={(value) => {
                    setYear(value)
                    setSemester("") // Reset semester when year changes
                  }}>
                    <SelectTrigger id="year">
                      <SelectValue placeholder="Select year" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1st">1st Year</SelectItem>
                      <SelectItem value="2nd">2nd Year</SelectItem>
                      <SelectItem value="3rd">3rd Year</SelectItem>
                      <SelectItem value="4th">4th Year</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Semester */}
                <div className="space-y-2">
                  <Label htmlFor="semester">Semester *</Label>
                  <Select value={semester} onValueChange={setSemester}>
                    <SelectTrigger id="semester">
                      <SelectValue placeholder="Select semester" />
                    </SelectTrigger>
                    <SelectContent>
                      {(year ? yearToSemesters[year] || [] : [1, 2, 3, 4, 5, 6, 7, 8]).map((sem) => (
                        <SelectItem key={sem} value={String(sem)}>
                          Semester {sem}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Department */}
                <div className="space-y-2">
                  <Label htmlFor="department">Department *</Label>
                  <Select value={department} onValueChange={setDepartment}>
                    <SelectTrigger id="department">
                      <SelectValue placeholder="Select department" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="CSE">Computer Science & Engineering</SelectItem>
                      <SelectItem value="ECE">Electronics & Communication</SelectItem>
                      <SelectItem value="EEE">Electrical & Electronics</SelectItem>
                      <SelectItem value="ME">Mechanical Engineering</SelectItem>
                      <SelectItem value="CE">Civil Engineering</SelectItem>
                      <SelectItem value="IT">Information Technology</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Section */}
                <div className="space-y-2">
                  <Label htmlFor="section">Section *</Label>
                  <Select value={section} onValueChange={setSection}>
                    <SelectTrigger id="section">
                      <SelectValue placeholder="Select section" />
                    </SelectTrigger>
                    <SelectContent>
                      {Array.from({ length: 26 }, (_, i) => String.fromCharCode(65 + i)).map((sec) => (
                        <SelectItem key={sec} value={sec}>
                          Section {sec}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Faculty Advisor Name */}
                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="facultyAdvisor">Faculty Advisor Name *</Label>
                  <Input
                    id="facultyAdvisor"
                    type="text"
                    placeholder="Enter faculty advisor name"
                    value={facultyAdvisor}
                    onChange={(e) => setFacultyAdvisor(e.target.value)}
                  />
                </div>

                {/* Batch */}
                <div className="space-y-2">
                  <Label htmlFor="batch">Batch (optional)</Label>
                  <Input
                    id="batch"
                    type="text"
                    placeholder="e.g. 2022–2026"
                    value={batch}
                    onChange={(e) => setBatch(e.target.value)}
                  />
                </div>

                {/* Exam Date */}
                <div className="space-y-2">
                  <Label htmlFor="examDate">Exam Date (optional)</Label>
                  <Input
                    id="examDate"
                    type="text"
                    placeholder="e.g. Nov / Dec 2025"
                    value={examDate}
                    onChange={(e) => setExamDate(e.target.value)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Upload Section */}
          {isFormComplete && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5" />
                  Upload Section Excel
                </CardTitle>
                <CardDescription>
                  Upload the consolidated Excel file containing all subjects' results for this section
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {uploadStatus ? (
                  // Already uploaded
                  <Alert className="bg-green-50 border-green-200">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                    <AlertDescription>
                      <p className="font-medium text-green-900">File uploaded successfully</p>
                      <p className="text-sm text-green-700 mt-1">
                        <span className="font-medium">File:</span> {uploadStatus.fileName}
                      </p>
                      <p className="text-sm text-green-700">
                        <span className="font-medium">Uploaded:</span>{" "}
                        {new Date(uploadStatus.uploadedAt).toLocaleString()}
                      </p>
                    </AlertDescription>
                  </Alert>
                ) : (
                  // Upload interface
                  <>
                    <div
                      className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${isDragging ? "border-primary bg-primary/5" : "border-muted-foreground/25"
                        }`}
                      onDragOver={(e) => {
                        e.preventDefault()
                        setIsDragging(true)
                      }}
                      onDragLeave={() => setIsDragging(false)}
                      onDrop={handleDrop}
                    >
                      <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                      <p className="text-sm font-medium mb-2">
                        {selectedFile ? selectedFile.name : "Drag and drop Excel file here"}
                      </p>
                      <p className="text-xs text-muted-foreground mb-4">or</p>
                      <Input
                        type="file"
                        accept=".xlsx,.xls"
                        onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                        className="hidden"
                        id="file-upload"
                      />
                      <Button variant="outline" asChild>
                        <label htmlFor="file-upload" className="cursor-pointer">
                          Browse Files
                        </label>
                      </Button>
                      <p className="text-xs text-muted-foreground mt-4">Accepted formats: .xlsx, .xls</p>
                    </div>

                    {uploadErrors.length > 0 && (
                      <Alert variant="destructive">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                          <p className="font-medium">Upload failed with the following errors:</p>
                          <ul className="list-disc list-inside mt-2 text-sm">
                            {uploadErrors.map((error, i) => (
                              <li key={i}>{error}</li>
                            ))}
                          </ul>
                        </AlertDescription>
                      </Alert>
                    )}

                    <Button
                      onClick={handleUpload}
                      disabled={!selectedFile || isUploading}
                      className="w-full bg-primary hover:bg-primary/90"
                      size="lg"
                    >
                      {isUploading ? "Uploading..." : "Upload Section Excel"}
                    </Button>
                  </>
                )}

                {/* Preview Report Button */}
                {uploadStatus && (
                  <Button onClick={handlePreviewReport} variant="outline" className="w-full bg-transparent" size="lg">
                    <FileCheck className="mr-2 h-5 w-5" />
                    Preview Final Report
                  </Button>
                )}
              </CardContent>
            </Card>
          )}

          {!isFormComplete && (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">Please fill in all section details above to enable file upload</p>
              </CardContent>
            </Card>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="text-center py-3 text-[11px] text-muted-foreground/60">
        Created by <span className="font-medium text-muted-foreground">Saransh Dutta</span> &amp; <span className="font-medium text-muted-foreground">Rituparna Ghosh</span>
      </footer>
    </div>
  )
}
