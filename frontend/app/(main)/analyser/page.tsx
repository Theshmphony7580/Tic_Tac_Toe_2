"use client";

import React, { useState, useRef, useCallback } from "react";
import { Upload, FileText, Trash2, CheckCircle, AlertCircle, ChevronDown } from "lucide-react";

/* ────────── types ────────── */
interface UploadedFile {
  id: string;
  name: string;
  size: number;
  progress: number;
  status: "uploading" | "done" | "error";
  errorMsg?: string;
  result?: any;
  abortController?: AbortController;
}

/* ────────── helpers ────────── */
function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

const ACCEPTED_EXTENSIONS = ".pdf,.docx,.txt";
const ACCEPTED_MIME =
  "application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain";

const ROLES = [
  "Frontend Engineer",
  "Backend Engineer",
  "Fullstack Engineer",
  "Data Scientist",
  "DevOps Engineer",
  "UI/UX Designer",
  "Product Manager"
];

/* ────────── component ────────── */
export default function AnalyserPage() {
  const [selectedRole, setSelectedRole] = useState(ROLES[0]);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  /* ── upload one file via XHR (so we get progress events) ── */
  const uploadFile = useCallback((file: File, currentRole: string) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    const abortController = new AbortController();

    const entry: UploadedFile = {
      id,
      name: file.name,
      size: file.size,
      progress: 0,
      status: "uploading",
      abortController,
    };

    setFiles((prev) => [...prev, entry]);

    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        const pct = Math.round((e.loaded / e.total) * 100);
        setFiles((prev) =>
          prev.map((f) => (f.id === id ? { ...f, progress: pct } : f))
        );
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const res = JSON.parse(xhr.responseText);
          setFiles((prev) =>
            prev.map((f) =>
              f.id === id
                ? { ...f, progress: 100, status: "done", result: res }
                : f
            )
          );
        } catch {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === id ? { ...f, progress: 100, status: "done", result: { message: "Success but invalid JSON response", raw: xhr.responseText } } : f
            )
          );
        }
      } else {
        setFiles((prev) =>
          prev.map((f) => (f.id === id ? { ...f, status: "error", errorMsg: `HTTP ${xhr.status}: ${xhr.statusText}` } : f))
        );
      }
    });

    xhr.addEventListener("error", () => {
      setFiles((prev) =>
        prev.map((f) => (f.id === id ? { ...f, status: "error", errorMsg: "Network Error" } : f))
      );
    });

    abortController.signal.addEventListener("abort", () => {
      xhr.abort();
    });

    const formData = new FormData();
    formData.append("file", file);
    // Even if BE doesn't strictly process 'role' yet, we pass it just in case
    formData.append("role", currentRole);

    // Endpoint must hit /api/v1/parse because gateway-service prefixes the parse router
    const gatewayUrl = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8000";
    xhr.open("POST", `${gatewayUrl}/api/v1/parse`);
    // Required by APIKeyMiddleware in gateway-service/app/middleware/auth.py
    xhr.setRequestHeader("X-API-Key", "sk_test_123");
    xhr.send(formData);
  }, []);

  /* ── handle files from input / drop ── */
  const handleFiles = useCallback(
    (fileList: FileList | null) => {
      if (!fileList) return;
      Array.from(fileList).forEach((f) => {
        const ext = f.name.split(".").pop()?.toLowerCase();
        if (["pdf", "docx", "txt"].includes(ext || "")) {
          uploadFile(f, selectedRole);
        }
      });
    },
    [uploadFile, selectedRole]
  );

  /* ── delete ── */
  const handleDelete = useCallback((file: UploadedFile) => {
    if (file.status === "uploading" && file.abortController) {
      file.abortController.abort();
    }
    setFiles((prev) => prev.filter((f) => f.id !== file.id));
  }, []);

  /* ── drag & drop ── */
  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  /* ────────── render ────────── */
  return (
    <div className="min-h-screen p-6 lg:p-10 bg-[#fdfcfb] font-sans text-gray-800">
      <div className="max-w-[720px] mx-auto space-y-8">
        
        <div className="mb-2">
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Resume Analyser</h1>
          <p className="text-sm text-gray-500 mt-1">Upload candidate resumes to extract insights instantly.</p>
        </div>

        {/* 1. Upload Resume Dropzone */}
        <div
          className={`relative flex flex-col items-center justify-center gap-3 p-10 border-2 border-dashed rounded-xl cursor-pointer transition-colors duration-200 ${
            isDragging
              ? "border-indigo-500 bg-indigo-50/50"
              : "border-gray-200 bg-white hover:border-indigo-400 hover:bg-gray-50/50"
          }`}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
        >
          <input
            ref={inputRef}
            type="file"
            accept={`${ACCEPTED_EXTENSIONS},${ACCEPTED_MIME}`}
            multiple
            className="hidden"
            onChange={(e) => {
              handleFiles(e.target.files);
              e.target.value = "";
            }}
          />

          <div className="w-14 h-14 flex items-center justify-center rounded-xl bg-indigo-100 text-indigo-600 mb-2">
            <Upload size={28} strokeWidth={1.8} />
          </div>

          <p className="text-sm text-gray-600 font-medium text-center">
            <span className="text-indigo-600 font-semibold cursor-pointer">Click to browse</span> or drag and drop files
          </p>
          <p className="text-xs text-gray-400">Supported: PDF, DOCX, TXT</p>
        </div>

        {/* 2. Select Role */}
        <div className="bg-white border border-gray-100 rounded-xl p-5 shadow-sm space-y-3">
          <label htmlFor="role-select" className="block text-sm font-semibold text-gray-700">
            Select Role for Keyword Matching
          </label>
          <div className="relative">
            <select
              id="role-select"
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              className="appearance-none w-full bg-gray-50 border border-gray-200 text-gray-700 py-3 px-4 pr-10 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-colors text-sm font-medium"
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-gray-500">
              <ChevronDown size={18} />
            </div>
          </div>
        </div>

        {/* 3. Upload Status */}
        {files.length > 0 && (
          <div className="bg-white border border-gray-100 rounded-xl p-5 shadow-sm space-y-4">
             <h3 className="text-sm font-semibold text-gray-700">Upload Status</h3>
             <ul className="flex flex-col gap-3">
              {files.map((file) => (
                <li
                  key={file.id}
                  className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg border border-gray-100"
                >
                  <div className="shrink-0 w-10 h-10 flex items-center justify-center bg-indigo-100/50 rounded-lg text-indigo-600">
                    <FileText size={20} strokeWidth={1.6} />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="text-sm font-semibold text-gray-800 truncate" title={file.name}>
                        {file.name}
                      </span>
                      <span className="text-xs font-semibold text-indigo-600 shrink-0">
                        {file.status === "error" ? (
                          <AlertCircle size={16} className="text-red-500" />
                        ) : file.status === "done" ? (
                          <CheckCircle size={16} className="text-green-500" />
                        ) : (
                          `${file.progress}%`
                        )}
                      </span>
                    </div>
                    {/* Status Text & Progress bar */}
                    {file.status === "error" ? (
                      <span className="text-xs text-red-500">{file.errorMsg}</span>
                    ) : (
                      <>
                        <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-300 ${
                               file.status === "done" ? "bg-green-500" : "bg-indigo-500"
                            }`}
                            style={{ width: `${file.progress}%` }}
                          />
                        </div>
                      </>
                    )}
                  </div>

                  <button
                    className="shrink-0 w-8 h-8 flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-md transition-colors"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(file);
                    }}
                    title="Remove file"
                  >
                    <Trash2 size={16} />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* 4. JSON Result of /parse Endpoint */}
        {files.some(f => f.status === "done" && f.result) && (
          <div className="bg-[#1e1e1e] rounded-xl shadow-lg border border-gray-800 overflow-hidden flex flex-col">
            <div className="bg-[#2d2d2d] px-4 py-3 border-b border-gray-700 flex items-center justify-between">
              <span className="text-xs font-semibold tracking-wider text-gray-300 uppercase">Parse Result (JSON)</span>
            </div>
            <div className="p-4 max-h-[600px] overflow-auto">
              <pre className="text-sm text-green-400 font-mono whitespace-pre-wrap word-break-all">
                {files
                  .filter(f => f.status === "done" && f.result)
                  .map(f => (
                    <div key={`result-${f.id}`} className="mb-6 last:mb-0">
                      <div className="text-gray-500 text-xs mb-2 border-b border-gray-700 pb-1">File: {f.name}</div>
                      {JSON.stringify(f.result, null, 2)}
                    </div>
                  ))}
              </pre>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
