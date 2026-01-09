import { Briefcase, Home, Users } from "lucide-react"
import { useTranslation } from "react-i18next"

import { SidebarAppearance, SidebarLanguage } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
} from "@/components/ui/sidebar"
import useAuth from "@/hooks/useAuth"
import { type Item, Main } from "./Main"
import { User } from "./User"

export function AppSidebar() {
  const { user: currentUser } = useAuth()
  const { t } = useTranslation("dashboard")

  const baseItems: Item[] = [
    { icon: Home, title: t("navigation.dashboard"), path: "/" },
    { icon: Briefcase, title: t("navigation.items"), path: "/items" },
  ]

  const items = currentUser?.is_superuser
    ? [...baseItems, { icon: Users, title: t("navigation.admin"), path: "/admin" }]
    : baseItems

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 py-6 group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:items-center">
        <Logo variant="responsive" />
      </SidebarHeader>
      <SidebarContent>
        <Main items={items} />
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          <SidebarLanguage />
          <SidebarAppearance />
        </SidebarMenu>
        <User user={currentUser} />
      </SidebarFooter>
    </Sidebar>
  )
}

export default AppSidebar
