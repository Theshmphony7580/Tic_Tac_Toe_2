"use client";

import React, { useState, useRef, useCallback } from "react";
import { Upload, FileText, Trash2, CheckCircle, AlertCircle } from "lucide-react";
/* ────────── types ────────── */
interface UploadedFile {
  id: string;
  name: string;
  size: number;
  storedName: string;
  progress: number;
  status: "uploading" | "done" | "error";
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

/* ────────── component ────────── */
export default function AnalyserPage() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  /* ── upload one file via XHR (so we get progress events) ── */
  const uploadFile = useCallback((file: File) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    const abortController = new AbortController();

    const entry: UploadedFile = {
      id,
      name: file.name,
      size: file.size,
      storedName: "",
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
                ? { ...f, progress: 100, status: "done", storedName: res.storedName }
                : f
            )
          );
        } catch {
          setFiles((prev) =>
            prev.map((f) => (f.id === id ? { ...f, status: "error" } : f))
          );
        }
      } else {
        setFiles((prev) =>
          prev.map((f) => (f.id === id ? { ...f, status: "error" } : f))
        );
      }
    });

    xhr.addEventListener("error", () => {
      setFiles((prev) =>
        prev.map((f) => (f.id === id ? { ...f, status: "error" } : f))
      );
    });

    abortController.signal.addEventListener("abort", () => {
      xhr.abort();
    });

    const formData = new FormData();
    formData.append("file", file);

    xhr.open("POST", "/api/upload");
    xhr.send(formData);
  }, []);

  /* ── handle files from input / drop ── */
  const handleFiles = useCallback(
    (fileList: FileList | null) => {
      if (!fileList) return;
      Array.from(fileList).forEach((f) => {
        const ext = f.name.split(".").pop()?.toLowerCase();
        if (["pdf", "docx", "txt"].includes(ext || "")) {
          uploadFile(f);
        }
      });
    },
    [uploadFile]
  );

  /* ── delete ── */
  const handleDelete = useCallback(async (file: UploadedFile) => {
    // Abort if still uploading
    if (file.status === "uploading" && file.abortController) {
      file.abortController.abort();
    }

    // Remove from server if uploaded
    if (file.status === "done" && file.storedName) {
      try {
        await fetch("/api/upload", {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ storedName: file.storedName }),
        });
      } catch {
        /* best effort */
      }
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
    <div className="min-h-screen flex items-start justify-center p-[3rem_1.5rem] bg-gradient-to-br from-[#f8f9fc] via-[#eef1f8] to-[#e8ecf6] max-sm:p-[1.25rem_1rem]">
      <div className="w-full max-w-[640px] bg-white rounded-[20px] shadow-[0_4px_32px_rgba(80,90,140,0.08),0_1.5px_6px_rgba(80,90,140,0.04)] p-[2.5rem_2.25rem_2rem] max-sm:p-[1.75rem_1.25rem_1.5rem] max-sm:rounded-[16px]">
        {/* Header */}
        <div className="mb-7">
          <h1 className="text-[1.65rem] font-bold text-[#1a1d2e] tracking-[-0.02em] m-0 mb-[0.35rem]">Upload Resume</h1>
          <p className="text-[0.92rem] text-[#6b7194] m-0 leading-relaxed">
            Upload your resume to get AI-powered insights and analysis.
          </p>
        </div>

        {/* Drop zone */}
        <div
          className={`relative flex flex-col items-center justify-center gap-[0.6rem] p-[2.75rem_2rem] border-2 border-dashed border-[#c5cbdf] rounded-[14px] cursor-pointer transition-[border-color,background,box-shadow] duration-250 ${
            isDragging
              ? "border-[#7c6ff5] bg-[#ede9ff] shadow-[0_0_0_4px_rgba(124,111,245,0.12)]"
              : "bg-[#fafafd] hover:border-[#7c6ff5] hover:bg-[#f5f3ff]"
          } max-sm:p-[2rem_1.25rem]`}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
          }}
          id="upload-drop-zone"
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
            id="file-input"
          />

          <div className="w-[52px] h-[52px] flex items-center justify-center rounded-[14px] bg-gradient-to-br from-[#7c6ff5] to-[#6354d9] text-white shadow-[0_4px_14px_rgba(124,111,245,0.3)] mb-1">
            <Upload size={28} strokeWidth={1.8} />
          </div>

          <p className="text-[0.95rem] text-[#4a4f6a] m-0">
            <span className="text-[#7c6ff5] font-semibold no-underline cursor-pointer hover:underline">Click here</span> to upload your
            file or drag.
          </p>
          <p className="text-[0.8rem] text-[#9a9fba] m-0">
            Supported Formats: PDF, DOCX, TXT (10MB each)
          </p>
        </div>

        {/* File list */}
        {files.length > 0 && (
          <ul className="list-none mt-6 mb-0 p-0 flex flex-col gap-3">
            {files.map((file) => (
              <li
                key={file.id}
                className="flex items-center gap-[0.85rem] p-[0.9rem_1rem] bg-[#fafafd] border border-[#e8ebf2] rounded-xl transition-all duration-200 hover:border-[#d0d4e4] hover:shadow-[0_2px_10px_rgba(80,90,140,0.06)]"
                id={`file-${file.id}`}
              >
                {/* icon */}
                <div className="shrink-0 w-[38px] h-[38px] flex items-center justify-center bg-gradient-to-br from-[#eceaff] to-[#e0dcff] rounded-[10px] text-[#7c6ff5]">
                  <FileText size={20} strokeWidth={1.6} />
                </div>

                {/* info + progress */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className="text-[0.88rem] font-semibold text-[#1a1d2e] whitespace-nowrap overflow-hidden text-ellipsis"
                      title={file.name}
                    >
                      {file.name}
                    </span>
                    <span className="text-[0.8rem] font-semibold text-[#7c6ff5] shrink-0">
                      {file.status === "error" ? (
                        <AlertCircle size={16} className="text-[#f25f5c]" />
                      ) : file.status === "done" ? (
                        <CheckCircle size={16} className="text-[#34c77b]" />
                      ) : (
                        `${file.progress}%`
                      )}
                    </span>
                  </div>
                  <span className="block text-[0.75rem] text-[#9a9fba] mt-[0.1rem]">
                    {formatBytes(file.size)}
                  </span>
                  {/* progress bar */}
                  <div className="h-[5px] bg-[#e8ebf2] rounded-full overflow-hidden mt-2">
                    <div
                      className={`h-full rounded-full transition-[width] duration-300 ease-in-out ${
                        file.status === "error"
                          ? "bg-gradient-to-r from-[#f25f5c] to-[#f78584]"
                          : file.status === "done"
                          ? "bg-gradient-to-r from-[#34c77b] to-[#49e098]"
                          : "bg-gradient-to-r from-[#7c6ff5] to-[#9b8fff]"
                      }`}
                      style={{ width: `${file.progress}%` }}
                    />
                  </div>
                </div>

                {/* delete */}
                <button
                  className="shrink-0 w-[34px] h-[34px] flex items-center justify-center border-none bg-transparent text-[#b0b5c9] rounded-[8px] cursor-pointer transition-colors duration-200 hover:text-[#f25f5c] hover:bg-[#fef2f2]"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(file);
                  }}
                  title="Remove file"
                  id={`delete-${file.id}`}
                >
                  <Trash2 size={18} strokeWidth={1.6} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
