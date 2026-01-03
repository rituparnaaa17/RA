import Image from "next/image"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

interface AppHeaderProps {
  facultyEmail?: string
}

export function AppHeader({ facultyEmail = "faculty@srmist.edu.in" }: AppHeaderProps) {
  const initials = facultyEmail
    .split("@")[0]
    .split(".")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between px-4 md:px-6">
        <div className="flex items-center gap-3">
          <Image src="/srm-logo.png" alt="SRM Institute Logo" width={48} height={48} className="h-12 w-12" />
          <div className="flex flex-col">
            <h1 className="text-lg font-semibold text-primary md:text-xl">SRM Result Analysis</h1>
            <p className="text-xs text-muted-foreground hidden sm:block">Faculty Portal</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden text-right sm:block">
            <p className="text-sm font-medium">Faculty</p>
            <p className="text-xs text-muted-foreground">{facultyEmail}</p>
          </div>
          <Avatar>
            <AvatarFallback className="bg-primary text-primary-foreground">{initials}</AvatarFallback>
          </Avatar>
        </div>
      </div>
    </header>
  )
}
