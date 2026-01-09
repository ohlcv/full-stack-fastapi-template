import { createFileRoute } from "@tanstack/react-router"
import { useTranslation } from "react-i18next"

import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: "Dashboard - FastAPI Cloud",
      },
    ],
  }),
})

function Dashboard() {
  const { t } = useTranslation("dashboard")
  const { user: currentUser } = useAuth()

  return (
    <div>
      <div>
        <h1 className="text-2xl truncate max-w-sm">
          {t("welcomeMessage", { name: currentUser?.full_name || currentUser?.email })} 👋
        </h1>
        <p className="text-muted-foreground">
          {t("welcome")}
        </p>
      </div>
    </div>
  )
}
