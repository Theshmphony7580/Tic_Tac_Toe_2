"use client";

import React, { useState } from "react";
import {
  AreaChart,
  Area,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip as RechartsTooltip,
} from "recharts";
import { Mail, Phone, Download, ChevronDown, ChevronUp, Briefcase, FileText } from "lucide-react";

// --- DUMMY DATA ---

const DUMMY_CANDIDATES = [
  {
    id: "#7854321",
    name: "Rohan Sharma",
    role: "Frontend Engineer",
    email: "rohan.sharma@example.com",
    phone: "+91 98765 43210",
    skillsMatch: 85,
    suitable: true,
    experience: "4 Years",
    source: "LinkedIn",
    appliedDate: "15 Dec, 2024",
  },
  {
    id: "#9876543",
    name: "Priya Patel",
    role: "Backend Developer",
    email: "priya.patel@example.com",
    phone: "+91 98765 43211",
    skillsMatch: 92,
    suitable: true,
    experience: "6 Years",
    source: "Naukri",
    appliedDate: "22 Dec, 2024",
  },
  {
    id: "#1234567",
    name: "Anjali Singh",
    role: "UI/UX Designer",
    email: "anjali.singh@example.com",
    phone: "+91 98765 43212",
    skillsMatch: 65,
    suitable: false,
    experience: "2 Years",
    source: "Direct",
    appliedDate: "18 Dec, 2024",
  },
  {
    id: "#3456789",
    name: "Vivek Kumar",
    role: "Fullstack Engineer",
    email: "vivek.kumar@example.com",
    phone: "+91 98765 43213",
    skillsMatch: 78,
    suitable: true,
    experience: "5 Years",
    source: "LinkedIn",
    appliedDate: "25 Dec, 2024",
  },
  {
    id: "#1112345",
    name: "Rajeev Iyer",
    role: "Data Scientist",
    email: "rajeev.iyer@example.com",
    phone: "+91 98765 43214",
    skillsMatch: 45,
    suitable: false,
    experience: "1 Year",
    source: "Indeed",
    appliedDate: "01 Dec, 2024",
  },
];

const GRAPH_DATA = [
  { name: "Mon", candidates: 12 },
  { name: "Tue", candidates: 19 },
  { name: "Wed", candidates: 15 },
  { name: "Thu", candidates: 25 },
  { name: "Fri", candidates: 22 },
  { name: "Sat", candidates: 10 },
  { name: "Sun", candidates: 5 },
];

export default function DashboardPage() {
  const [expandedRowId, setExpandedRowId] = useState<string | null>(null);

  const toggleRow = (id: string) => {
    if (expandedRowId === id) {
      setExpandedRowId(null);
    } else {
      setExpandedRowId(id);
    }
  };

  const totalCandidates = 154;
  const suitableCandidates = 89;

  return (
    <div className="w-full min-h-full bg-[#fdfcfb] p-6 lg:p-10 font-sans text-gray-800">
      <div className="max-w-[1400px] mx-auto space-y-8">

        {/* Header Section */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Candidates Overview</h1>
            <p className="text-sm text-gray-500 mt-1">Review and manage recent applications</p>
          </div>
        </div>

        {/* Top Cards Section (Architectural mapping to Image 1) */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {/* Total Candidates Card */}
          <div className="bg-white border text-center border-gray-100 rounded-xl p-6 shadow-sm flex flex-col justify-center items-center h-[160px] hover:shadow-md transition-shadow">
            <p className="text-sm font-medium text-gray-500 uppercase tracking-widest mb-2">Total Candidates</p>
            <p className="text-5xl font-semibold text-gray-900">{totalCandidates}</p>
          </div>

          {/* Suitable Candidates Card */}
          <div className="bg-white border text-center border-gray-100 rounded-xl p-6 shadow-sm flex flex-col justify-center items-center h-[160px] hover:shadow-md transition-shadow">
            <p className="text-sm font-medium text-gray-500 uppercase tracking-widest mb-2">Suitable Candidates</p>
            <div className="flex items-baseline space-x-2">
              <p className="text-5xl font-semibold text-green-600">{suitableCandidates}</p>
              <span className="text-sm text-green-700 font-medium bg-green-50 px-2 py-1 rounded-full">&gt; 70% Score</span>
            </div>
          </div>

          {/* Graph Card */}
          <div className="bg-white border border-gray-100 rounded-xl p-6 shadow-sm h-[160px] md:col-span-1 lg:col-span-2 relative hover:shadow-md transition-shadow flex flex-col">
            <p className="text-sm font-medium text-gray-500 uppercase tracking-widest mb-4">Application Trends</p>
            <div className="flex-1 w-full relative">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={GRAPH_DATA}>
                  <defs>
                    <linearGradient id="colorCand" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="#4f46e5" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <RechartsTooltip
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    labelStyle={{ display: 'none' }}
                    itemStyle={{ color: '#4f46e5', fontWeight: 600 }}
                  />
                  <Area type="monotone" dataKey="candidates" stroke="#4f46e5" strokeWidth={3} fillOpacity={1} fill="url(#colorCand)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* List Section */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          {/* Table Header */}
          <div className="grid grid-cols-12 gap-4 p-4 border-b border-gray-100 bg-gray-50/50 text-xs font-semibold text-gray-500 uppercase tracking-wider">
            <div className="col-span-2 pl-2">ID</div>
            <div className="col-span-3">Name</div>
            <div className="col-span-3">Role</div>
            <div className="col-span-3">Email</div>
            <div className="col-span-1 text-right pr-2">Skills Match</div>
          </div>

          {/* Table Body */}
          <div className="divide-y divide-gray-50">
            {DUMMY_CANDIDATES.map((candidate) => {
              const isExpanded = expandedRowId === candidate.id;

              return (
                <div key={candidate.id} className={`flex flex-col transition-colors ${isExpanded ? 'bg-indigo-50/20' : 'hover:bg-gray-50/30'}`}>
                  {/* Main Row */}
                  <div
                    className="grid grid-cols-12 gap-4 p-4 cursor-pointer items-center text-sm"
                    onClick={() => toggleRow(candidate.id)}
                  >
                    <div className="col-span-2 font-medium text-gray-500 hover:text-indigo-600 transition-colors pl-2">
                      {candidate.id}
                    </div>
                    <div className="col-span-3 font-medium text-gray-900">
                      {candidate.name}
                    </div>
                    <div className="col-span-3">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        {candidate.role}
                      </span>
                    </div>
                    <div className="col-span-3 text-gray-500">
                      {candidate.email}
                    </div>
                    <div className="col-span-1 flex justify-end items-center space-x-3 pr-2">
                      <span className={`inline-flex font-semibold ${candidate.skillsMatch >= 70 ? 'text-green-600' : 'text-amber-600'}`}>
                        {candidate.skillsMatch}%
                      </span>
                      <div className="text-gray-400">
                        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </div>
                    </div>
                  </div>

                  {/* Expanded Details Row */}
                  {isExpanded && (
                    <div className="p-4 pt-0">
                      <div className="mt-2 p-6 rounded-xl border border-indigo-100 bg-white grid grid-cols-1 lg:grid-cols-3 gap-6 shadow-sm overflow-hidden relative">

                        {/* Personal Details */}
                        <div className="flex flex-col space-y-4">
                          <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide border-b border-gray-100 pb-2">Personal Details</h3>
                          <div className="space-y-3">
                            <div className="flex items-center text-sm">
                              <Briefcase className="w-4 h-4 text-gray-400 mr-3" />
                              <span className="text-gray-600 w-24">Experience:</span>
                              <span className="font-medium text-gray-900">{candidate.experience}</span>
                            </div>
                            <div className="flex items-center text-sm">
                              <Phone className="w-4 h-4 text-gray-400 mr-3" />
                              <span className="text-gray-600 w-24">Phone:</span>
                              <span className="font-medium text-gray-900">{candidate.phone}</span>
                            </div>
                            <div className="flex items-center text-sm">
                              <Mail className="w-4 h-4 text-gray-400 mr-3" />
                              <span className="text-gray-600 w-24">Email:</span>
                              <span className="font-medium text-gray-900">{candidate.email}</span>
                            </div>
                            <div className="flex items-center text-sm">
                              {/* <ExternalLink className="w-4 h-4 text-gray-400 mr-3" /> */}
                              <span className="text-gray-600 w-24">Source:</span>
                              <span className="font-medium text-gray-900">{candidate.source}</span>
                            </div>
                          </div>
                        </div>

                        {/* Skills Matched (Pie Chart) */}
                        <div className="flex flex-col space-y-4 lg:border-x lg:border-gray-100 lg:px-6">
                          <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide border-b border-gray-100 pb-2">Skills Match</h3>
                          <div className="flex items-center justify-between h-full pb-4">
                            <div className="flex-1">
                              <p className="text-3xl font-bold mb-1" style={{ color: candidate.skillsMatch >= 70 ? '#16a34a' : '#d97706' }}>
                                {candidate.skillsMatch}%
                              </p>
                              <p className="text-xs text-gray-500 uppercase tracking-wider">Overall Match Score</p>
                            </div>
                            <div className="w-[100px] h-[100px]">
                              <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                  <Pie
                                    data={[
                                      { name: 'Matched', value: candidate.skillsMatch },
                                      { name: 'Unmatched', value: 100 - candidate.skillsMatch }
                                    ]}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={30}
                                    outerRadius={45}
                                    stroke="none"
                                    dataKey="value"
                                    startAngle={90}
                                    endAngle={-270}
                                  >
                                    <Cell fill={candidate.skillsMatch >= 70 ? '#16a34a' : '#d97706'} />
                                    <Cell fill="#f3f4f6" />
                                  </Pie>
                                </PieChart>
                              </ResponsiveContainer>
                            </div>
                          </div>
                        </div>

                        {/* Actions & Resume */}
                        <div className="flex flex-col space-y-4">
                          <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide border-b border-gray-100 pb-2">Actions</h3>
                          <div className="flex-1 flex flex-col justify-center space-y-3 pb-2">
                            <a href="#" className="flex px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors items-center justify-center">
                              <FileText className="w-4 h-4 mr-2" />
                              View Resume
                            </a>
                            <a href={`mailto:${candidate.email}`} className="flex px-4 py-2.5 border border-gray-200 hover:border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg text-sm font-medium transition-colors items-center justify-center">
                              <Mail className="w-4 h-4 mr-2" />
                              Send Email Message
                            </a>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
}
