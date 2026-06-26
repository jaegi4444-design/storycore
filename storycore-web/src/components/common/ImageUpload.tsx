import { useRef, useState } from 'react';
import { validateImageFile } from '../../lib/characterImage';
import { Button } from './Button';

type ImageUploadProps = {
  label?: string;
  currentImageUrl?: string | null;
  onChange: (file: File | null, remove: boolean) => void;
};

export function ImageUpload({ label = '캐릭터 이미지', currentImageUrl, onChange }: ImageUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [removed, setRemoved] = useState(false);

  const displayUrl = removed ? null : (preview ?? currentImageUrl ?? null);

  const handleFile = (file: File | null) => {
    if (!file) return;
    const validationError = validateImageFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    setRemoved(false);
    setPreview(URL.createObjectURL(file));
    onChange(file, false);
  };

  const handleRemove = () => {
    setPreview(null);
    setRemoved(true);
    setError(null);
    onChange(null, true);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-300">{label}</label>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
        <div className="flex h-32 w-32 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-surface-border bg-surface-overlay">
          {displayUrl ? (
            <img src={displayUrl} alt="캐릭터 미리보기" className="h-full w-full object-cover" />
          ) : (
            <svg className="h-12 w-12 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          )}
        </div>
        <div className="flex flex-col gap-2">
          <input
            ref={inputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
          />
          <Button type="button" variant="secondary" onClick={() => inputRef.current?.click()}>
            이미지 선택
          </Button>
          {(displayUrl || currentImageUrl) && !removed && (
            <Button type="button" variant="ghost" className="text-red-400" onClick={handleRemove}>
              이미지 제거
            </Button>
          )}
          <p className="text-xs text-gray-500">JPEG, PNG, WebP, GIF · 최대 5MB</p>
          {error && <p className="text-xs text-red-400">{error}</p>}
        </div>
      </div>
    </div>
  );
}
