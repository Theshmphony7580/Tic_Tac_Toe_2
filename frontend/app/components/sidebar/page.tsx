"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Home, PenLine, LogOut, RefreshCw, UserRound } from "lucide-react";
import { useAuth } from "@/app/contexts/AuthContext";
import ChevronIcon from "../icons/ChevronIcon";

const navItems = [
  { label: "Dashboard", icon: Home, href: "/dashboard" },
  { label: "Analyser", icon: PenLine, href: "/analyser" },
];

export default function Sidebar() {
  const [open, setOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const sidebarRef = useRef<HTMLElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Use global auth state instead of local fetches
  const { user, logout } = useAuth();

  // Close sidebar when clicking outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (sidebarRef.current && !sidebarRef.current.contains(e.target as Node)) {
        setOpen(false);
        setMenuOpen(false);
      }
    }
    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [open]);

  // Close menu popover when clicking outside of it
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    if (menuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [menuOpen]);

  const handleMouseEnter = useCallback(() => {
    setOpen(true);
  }, []);

  const handleMouseLeave = useCallback(() => {
    setOpen(false);
    setMenuOpen(false);
  }, []);

  async function handleLogout() {
    await logout();
  }

  async function handleSwitchAccount() {
    await logout();
  }

  function getInitials(name: string) {
    return name
      .split(" ")
      .map((w) => w[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  }

  const displayName = user?.name || "User";

  return (
    <aside
      ref={sidebarRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      style={{ width: open ? 224 : 64 }}
      className={`h-screen bg-white border-r border-gray-200
                 flex flex-col justify-between fixed left-0 top-0 z-[60]
                 transition-[width] duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] ${menuOpen ? "overflow-visible" : "overflow-hidden"}`}
    >
      {/* Inner wrapper — fixed width so children don't reflow during animation */}
      <div className="flex flex-col justify-between h-full" style={{ minWidth: 224 }}>

        {/* TOP SECTION */}
        <div>
          {/* Toggle Button */}
          <button
            onClick={() => setOpen(!open)}
            className="p-4 transition"
          >
            <ChevronIcon
              className={`w-6 h-6 text-gray-700 transition-transform duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] ${open ? "rotate-180" : ""}`}
            />
          </button>

          {/* NAVIGATION */}
          <nav className="mt-10 flex flex-col gap-6 px-2">
            {navItems.map((item) => (
              <Link
                key={item.label}
                href={item.href}
                className="flex items-center gap-4 px-3 py-2 rounded-md hover:bg-gray-100 transition-colors text-gray-700"
              >
                <item.icon className="w-[22px] h-[22px] shrink-0" strokeWidth={1.5} />
                <span className="text-sm font-medium whitespace-nowrap px-2">
                  {item.label}
                </span>
              </Link>
            ))}
          </nav>
        </div>

        {/* BOTTOM SECTION — User Avatar */}
        <div className="relative px-2 pb-4" ref={menuRef}>
          {/* Popover Menu */}
          {menuOpen && (
            <div className="absolute bottom-full left-2 right-2 mb-2 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-red-50 hover:text-red-600 transition-colors"
              >
                <LogOut className="w-4 h-4 shrink-0" strokeWidth={1.5} />
                Logout
              </button>
              <button
                onClick={handleSwitchAccount}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-colors"
              >
                <RefreshCw className="w-4 h-4 shrink-0" strokeWidth={1.5} />
                Switch Account
              </button>
            </div>
          )}

          {/* Avatar Button */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex items-center gap-3 w-full rounded-lg py-2 px-3 hover:bg-gray-100 transition-colors"
          >
            {/* Avatar Circle — fixed size, never shrinks */}
            <div className="w-8 h-8 shrink-0">
              {user?.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt={displayName}
                  className="w-8 h-8 rounded-full object-cover shadow-sm"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="w-8 h-8 rounded-full bg-gray-100 border border-gray-200 flex items-center justify-center shadow-sm">
                  {user ? (
                    <span className="text-xs font-semibold text-gray-700 leading-none">
                      {getInitials(displayName)}
                    </span>
                  ) : (
                    <UserRound className="w-4 h-4 text-gray-500" strokeWidth={1.5} />
                  )}
                </div>
              )}
            </div>

            {/* Username — always in DOM, clipped by sidebar overflow:hidden */}
            {user && (
              <div className="flex flex-col items-start overflow-hidden">
                <span className="text-sm font-medium text-gray-800 whitespace-nowrap leading-tight">
                  {displayName}
                </span>
                <span className="text-[11px] text-gray-500 whitespace-nowrap leading-tight">
                  {user.email}
                </span>
              </div>
            )}
          </button>
        </div>
      </div>
    </aside>
  );
}
