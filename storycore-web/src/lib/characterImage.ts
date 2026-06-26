import { CHARACTER_IMAGES_BUCKET, supabase } from './supabase';

const MAX_IMAGE_SIZE = 5 * 1024 * 1024;
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];

export function validateImageFile(file: File): string | null {
  if (!ALLOWED_TYPES.includes(file.type)) {
    return 'JPEG, PNG, WebP, GIF 형식만 업로드할 수 있습니다.';
  }
  if (file.size > MAX_IMAGE_SIZE) {
    return '이미지 크기는 5MB 이하여야 합니다.';
  }
  return null;
}

export function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(new Error('이미지를 읽을 수 없습니다.'));
    reader.readAsDataURL(file);
  });
}

function getExtension(file: File): string {
  const fromName = file.name.split('.').pop()?.toLowerCase();
  if (fromName && ['jpg', 'jpeg', 'png', 'webp', 'gif'].includes(fromName)) {
    return fromName === 'jpeg' ? 'jpg' : fromName;
  }
  const map: Record<string, string> = {
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'image/webp': 'webp',
    'image/gif': 'gif',
  };
  return map[file.type] ?? 'jpg';
}

export async function uploadCharacterImage(
  userId: string,
  characterId: string,
  file: File,
): Promise<string> {
  const ext = getExtension(file);
  const path = `${userId}/${characterId}.${ext}`;

  const { error } = await supabase.storage
    .from(CHARACTER_IMAGES_BUCKET)
    .upload(path, file, { upsert: true, contentType: file.type });

  if (error) throw error;

  const { data } = supabase.storage.from(CHARACTER_IMAGES_BUCKET).getPublicUrl(path);
  return `${data.publicUrl}?t=${Date.now()}`;
}

export async function deleteCharacterImageByUrl(imageUrl: string): Promise<void> {
  const path = extractStoragePath(imageUrl);
  if (!path) return;

  const { error } = await supabase.storage.from(CHARACTER_IMAGES_BUCKET).remove([path]);
  if (error) throw error;
}

function extractStoragePath(imageUrl: string): string | null {
  try {
    const url = new URL(imageUrl);
    const marker = `/storage/v1/object/public/${CHARACTER_IMAGES_BUCKET}/`;
    const idx = url.pathname.indexOf(marker);
    if (idx === -1) return null;
    return decodeURIComponent(url.pathname.slice(idx + marker.length).split('?')[0]);
  } catch {
    return null;
  }
}
