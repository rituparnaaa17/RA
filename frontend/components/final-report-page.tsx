"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ArrowLeft, Download, Printer } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import Image from "next/image"

interface FinalReportPageProps {
  reportData: any
  onBack: () => void
}

export function FinalReportPage({ reportData, onBack }: FinalReportPageProps) {
  const { toast } = useToast()

  if (!reportData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Button onClick={onBack}>Back to Dashboard</Button>
      </div>
    )
  }

  const handlePrint = () => {
    window.print()
  }

  const handleDownloadPDF = () => {
    toast({
      title: "Generating PDF",
      description: "Your report is being prepared for download.",
    })
  }

  const { sectionDetails, subjects, summary } = reportData

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      {/* Action Bar - Hidden during print */}
      <div className="max-w-6xl mx-auto mb-6 flex flex-wrap items-center justify-between gap-4 print:hidden">
        <Button variant="ghost" onClick={onBack}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Dashboard
        </Button>
        <div className="flex gap-2">
          <Button onClick={handleDownloadPDF} variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Download PDF
          </Button>
          <Button onClick={handlePrint} className="bg-primary hover:bg-primary/90">
            <Printer className="mr-2 h-4 w-4" />
            Print Report
          </Button>
        </div>
      </div>

      {/* Report Container - A4 Paper Style */}
      <div className="max-w-6xl mx-auto bg-white shadow-sm border p-8 print:shadow-none print:border-none print:p-0">
        {/* SRM Header */}
        <div className="flex items-center justify-center gap-6 border-b-2 border-primary pb-6 mb-8">
          <Image src="/srm-logo.png" alt="SRM Logo" width={80} height={80} />
          <div className="text-center">
            <h1 className="text-2xl font-bold text-primary uppercase">SRM Institute of Science and Technology</h1>
            <p className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
              College of Engineering and Technology
            </p>
            <p className="text-lg font-bold mt-1">Consolidated Section Result Analysis</p>
          </div>
        </div>

        {/* Section Metadata Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6 mb-8 text-sm">
          <div className="space-y-1">
            <p className="text-muted-foreground">Department</p>
            <p className="font-bold text-base">{sectionDetails.department}</p>
          </div>
          <div className="space-y-1">
            <p className="text-muted-foreground">Year / Semester</p>
            <p className="font-bold text-base">
              {sectionDetails.year} Year / Sem {sectionDetails.semester}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-muted-foreground">Section</p>
            <p className="font-bold text-base">Section {sectionDetails.section}</p>
          </div>
          <div className="space-y-1">
            <p className="text-muted-foreground">Faculty Advisor</p>
            <p className="font-bold text-base">{sectionDetails.facultyAdvisor}</p>
          </div>
          <div className="space-y-1">
            <p className="text-muted-foreground">Total Students</p>
            <p className="font-bold text-base">{summary.totalStudents}</p>
          </div>
          <div className="space-y-1">
            <p className="text-muted-foreground">Overall Pass %</p>
            <p className="font-bold text-base text-primary">{summary.overallPassPercentage}%</p>
          </div>
        </div>

        {/* Main Subject-wise Analysis Table */}
        <Card className="rounded-none shadow-none border">
          <CardHeader className="bg-muted/50 py-3 border-b">
            <CardTitle className="text-base font-bold">Subject-wise Performance Analysis</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/30">
                    <TableHead className="font-bold text-black border-r">Subject Name</TableHead>
                    <TableHead className="text-right font-bold text-black border-r">Total Students</TableHead>
                    <TableHead className="text-right font-bold text-black border-r">Appeared</TableHead>
                    <TableHead className="text-right font-bold text-black border-r text-destructive">Failed</TableHead>
                    <TableHead className="text-right font-bold text-black border-r text-primary">Pass %</TableHead>
                    <TableHead className="text-right font-bold text-black">Avg CGPA</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {subjects.map((subject: any) => (
                    <TableRow key={subject.subjectCode} className="border-b">
                      <TableCell className="font-medium border-r">
                        {subject.subjectName} ({subject.subjectCode})
                      </TableCell>
                      <TableCell className="text-right border-r">{subject.totalStudents}</TableCell>
                      <TableCell className="text-right border-r">{subject.studentsAppeared}</TableCell>
                      <TableCell className="text-right border-r font-medium text-destructive">
                        {subject.studentsFailed}
                      </TableCell>
                      <TableCell className="text-right border-r font-bold text-primary">
                        {subject.passPercentage}%
                      </TableCell>
                      <TableCell className="text-right font-medium">{subject.averageCGPA}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Signature Section - Visible for print */}
        <div className="mt-16 grid grid-cols-2 gap-20 print:flex print:justify-between">
          <div className="text-center pt-4 border-t border-black w-48">
            <p className="text-sm font-bold uppercase">Faculty Advisor</p>
          </div>
          <div className="text-center pt-4 border-t border-black w-48 ml-auto">
            <p className="text-sm font-bold uppercase">Head of Department</p>
          </div>
        </div>

        <div className="mt-12 text-center text-[10px] text-muted-foreground print:block hidden">
          <p>Generated on {new Date().toLocaleString()} | SRM Result Analysis System</p>
        </div>
      </div>

      <style jsx global>{`
        @media print {
          body {
            background-color: white !important;
          }
          @page {
            size: A4;
            margin: 1.5cm;
          }
          .print-hidden {
            display: none !important;
          }
        }
      `}</style>
    </div>
  )
}
