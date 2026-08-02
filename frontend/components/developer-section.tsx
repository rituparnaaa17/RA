"use client"

import Image from "next/image"
import { Card, CardContent } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Info } from "lucide-react"

interface DeveloperInfo {
  name: string
  imageSrc: string
  imageAlt: string
  department: string
  section: string
  batch: string
}

const developers: DeveloperInfo[] = [
  {
    name: "Saransh Dutta",
    imageSrc: "/dev-saransh.jpg",
    imageAlt: "Saransh Dutta – Developer of SRM Result Analysis",
    department: "Computer Science",
    section: "Section P",
    batch: "2024–2028",
  },
  {
    name: "Rituparna Ghosh",
    imageSrc: "/dev-rituparna.jpg",
    imageAlt: "Rituparna Ghosh – Developer of SRM Result Analysis",
    department: "Information Technology",
    section: "Section B",
    batch: "2024–2028",
  },
]

function DeveloperCard({ developer }: { developer: DeveloperInfo }) {
  return (
    <Card className="group transition-shadow duration-300 hover:shadow-lg">
      <CardContent className="flex flex-col items-center text-center pt-8 pb-8">
        {/* Circular profile photo */}
        <div className="relative h-28 w-28 overflow-hidden rounded-full border-4 border-primary/20 shadow-md mb-4 transition-transform duration-300 group-hover:scale-105">
          <Image
            src={developer.imageSrc}
            alt={developer.imageAlt}
            fill
            className="object-cover"
            sizes="112px"
          />
        </div>

        {/* Name */}
        <h3 className="text-lg font-bold text-primary">{developer.name}</h3>

        {/* Department */}
        <p className="text-sm text-foreground mt-1">{developer.department}</p>

        {/* Section */}
        <p className="text-sm text-foreground">{developer.section}</p>

        {/* Batch */}
        <p className="text-xs text-muted-foreground mt-1">
          Batch: {developer.batch}
        </p>
      </CardContent>
    </Card>
  )
}

export function DeveloperPortal() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          type="button"
          aria-label="Developer information"
          className="flex items-center justify-center rounded-full border border-border bg-background/80 p-1.5 text-muted-foreground shadow-sm backdrop-blur transition-all duration-300 hover:border-primary/40 hover:text-primary hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <Info className="h-4 w-4" />
        </button>
      </DialogTrigger>

      <DialogContent className="sm:max-w-2xl">
        <DialogHeader className="text-center sm:text-center">
          <DialogTitle className="text-xl font-bold text-primary">
            Developers
          </DialogTitle>
          <DialogDescription>
            Built with care by the team behind this project
          </DialogDescription>
        </DialogHeader>

        {/* Two-column developer cards */}
        <div className="grid gap-6 sm:grid-cols-2 mt-2">
          {developers.map((dev) => (
            <DeveloperCard key={dev.name} developer={dev} />
          ))}
        </div>
      </DialogContent>
    </Dialog>
  )
}
