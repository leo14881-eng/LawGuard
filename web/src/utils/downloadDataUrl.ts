/** 触发浏览器下载一个 dataURL 内容为本地文件，纯前端操作，不经过任何网络请求。 */
export function downloadDataUrl(dataUrl: string, filename: string): void {
  const link = document.createElement('a')
  link.href = dataUrl
  link.download = filename
  link.click()
}
