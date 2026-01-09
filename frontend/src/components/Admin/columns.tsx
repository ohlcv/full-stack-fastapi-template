import type { ColumnDef } from "@tanstack/react-table"
import { useTranslation } from "react-i18next"

import type { UserPublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { UserActionsMenu } from "./UserActionsMenu"

export type UserTableData = UserPublic & {
  isCurrentUser: boolean
}

export function useUserColumns(): ColumnDef<UserTableData>[] {
  const { t } = useTranslation("users")

  return [
    {
      accessorKey: "full_name",
      header: t("table.fullName"),
      cell: ({ row }) => {
        const fullName = row.original.full_name
        return (
          <div className="flex items-center gap-2">
            <span
              className={cn("font-medium", !fullName && "text-muted-foreground")}
            >
              {fullName || "N/A"}
            </span>
            {row.original.isCurrentUser && (
              <Badge variant="outline" className="text-xs">
                You
              </Badge>
            )}
          </div>
        )
      },
    },
    {
      accessorKey: "email",
      header: t("table.email"),
      cell: ({ row }) => (
        <span className="text-muted-foreground">{row.original.email}</span>
      ),
    },
    {
      accessorKey: "is_superuser",
      header: t("table.role"),
      cell: ({ row }) => (
        <Badge variant={row.original.is_superuser ? "default" : "secondary"}>
          {row.original.is_superuser ? t("roles.superuser") : t("roles.user")}
        </Badge>
      ),
    },
    {
      accessorKey: "is_active",
      header: t("table.status"),
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "size-2 rounded-full",
              row.original.is_active ? "bg-green-500" : "bg-gray-400",
            )}
          />
          <span className={row.original.is_active ? "" : "text-muted-foreground"}>
            {row.original.is_active ? t("status.active") : t("status.inactive")}
          </span>
        </div>
      ),
    },
    {
      id: "actions",
      header: () => <span className="sr-only">{t("table.actions")}</span>,
      cell: ({ row }) => (
        <div className="flex justify-end">
          <UserActionsMenu user={row.original} />
        </div>
      ),
    },
  ]
}
