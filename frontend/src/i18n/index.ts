import i18n from "i18next"
import { initReactI18next } from "react-i18next"

// Import translation files
import enUSCommon from "./locales/en_US/common.json"
import enUSAuth from "./locales/en_US/auth.json"
import enUSDashboard from "./locales/en_US/dashboard.json"
import enUSItems from "./locales/en_US/items.json"
import enUSUsers from "./locales/en_US/users.json"
import enUSSettings from "./locales/en_US/settings.json"
import enUSValidation from "./locales/en_US/validation.json"

import zhCNCommon from "./locales/zh_CN/common.json"
import zhCNAuth from "./locales/zh_CN/auth.json"
import zhCNDashboard from "./locales/zh_CN/dashboard.json"
import zhCNItems from "./locales/zh_CN/items.json"
import zhCNUsers from "./locales/zh_CN/users.json"
import zhCNSettings from "./locales/zh_CN/settings.json"
import zhCNValidation from "./locales/zh_CN/validation.json"

// Supported languages
export const supportedLanguages = [
  { code: "zh_CN", name: "简体中文", flag: "🇨🇳" },
  { code: "en_US", name: "English", flag: "🇺🇸" },
] as const

export type LanguageCode = (typeof supportedLanguages)[number]["code"]

// Get default language from localStorage or browser settings
const getDefaultLanguage = (): LanguageCode => {
  // Check localStorage first
  const stored = localStorage.getItem("language")
  if (stored && supportedLanguages.some((l) => l.code === stored)) {
    return stored as LanguageCode
  }

  // Check browser language
  const browserLang = navigator.language
  if (browserLang.startsWith("zh")) {
    return "zh_CN"
  }

  return "en_US"
}

// Resources
const resources = {
  en_US: {
    common: enUSCommon,
    auth: enUSAuth,
    dashboard: enUSDashboard,
    items: enUSItems,
    users: enUSUsers,
    settings: enUSSettings,
    validation: enUSValidation,
  },
  zh_CN: {
    common: zhCNCommon,
    auth: zhCNAuth,
    dashboard: zhCNDashboard,
    items: zhCNItems,
    users: zhCNUsers,
    settings: zhCNSettings,
    validation: zhCNValidation,
  },
}

// Initialize i18next
i18n.use(initReactI18next).init({
  resources,
  lng: getDefaultLanguage(),
  fallbackLng: "en_US",
  defaultNS: "common",
  ns: ["common", "auth", "dashboard", "items", "users", "settings", "validation"],
  interpolation: {
    escapeValue: false, // React already escapes values
  },
  react: {
    useSuspense: false, // Disable suspense for better compatibility
  },
})

// Helper function to change language
export const changeLanguage = (lng: LanguageCode) => {
  i18n.changeLanguage(lng)
  localStorage.setItem("language", lng)
  // Update document language attribute
  document.documentElement.lang = lng.replace("_", "-")
}

// Get current language
export const getCurrentLanguage = (): LanguageCode => {
  return i18n.language as LanguageCode
}

export default i18n
