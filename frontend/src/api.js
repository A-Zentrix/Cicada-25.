const jsonHeaders = { Accept: 'application/json' };

export async function postForm(path, formData) {
  const res = await fetch(path, { method: 'POST', body: formData });
  return res.json();
}

export async function postJson(path, data) {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...jsonHeaders },
    body: JSON.stringify(data ?? {}),
  });
  return res.json();
}

export async function getJson(path) {
  const res = await fetch(path, { headers: jsonHeaders });
  return res.json();
}

export async function download(path, filename) {
  const res = await fetch(path);
  if (!res.ok) throw new Error('Download failed');
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}


