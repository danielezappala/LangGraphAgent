"use client";

import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { LogOut, Settings, User } from "lucide-react";
import { SidebarTrigger } from "@/components/ui/sidebar";

export function TopNav() {
  return (
    <header className="flex h-14 items-center gap-4 border-b bg-muted/40 px-4 lg:h-[60px] lg:px-6 sticky top-0 z-20">
      <SidebarTrigger className="md:hidden" />
      <div className="w-full flex-1">
        {/* Can have a search bar here if needed */}
      </div>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="secondary" size="icon" className="rounded-full">
            <Avatar className="h-8 w-8">
              <AvatarImage src="https://placehold.co/40x40" alt="User avatar" data-ai-hint="person face" />
              <AvatarFallback>U</AvatarFallback>
            </Avatar>
            <span className="sr-only">Toggle user menu</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>My Account</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem><User className="mr-2 h-4 w-4" /><span>Profile</span></DropdownMenuItem>
          <DropdownMenuItem><Settings className="mr-2 h-4 w-4" /><span>Settings</span></DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem><LogOut className="mr-2 h-4 w-4" /><span>Logout</span></DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}
