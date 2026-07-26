/**
 * 生成统一的公益分享卡片图片（PNG，1200×630，社交分享常用比例）。
 * 完全在浏览器本地通过 Canvas API 绘制，不上传任何内容到服务器，
 * 不包含联系人记录、用户选择的关系/案件阶段或任何案件材料。
 */
import QRCode from 'qrcode'

const WIDTH = 1200
const HEIGHT = 630
const FONT_FAMILY = '"Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif'

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('二维码图片加载失败'))
    img.src = src
  })
}

/**
 * @param shareUrl 卡片底部展示并编码进二维码的地址；调用方需保证该地址不含用户
 *   本地状态（关系/案件阶段/联系人等），只使用页面的规范路径。
 */
export async function generateShareCard(shareUrl: string): Promise<string> {
  const canvas = document.createElement('canvas')
  canvas.width = WIDTH
  canvas.height = HEIGHT
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    throw new Error('当前环境不支持 Canvas，无法生成分享图片')
  }

  // 背景：白底 + 顶部浅蓝灰色块，呼应 Design Tokens 中的 --color-surface/--color-bg
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, WIDTH, HEIGHT)
  ctx.fillStyle = '#eef2f7'
  ctx.fillRect(0, 0, WIDTH, 190)

  // 标题与副标题
  ctx.fillStyle = '#0b2545'
  ctx.font = `700 58px ${FONT_FAMILY}`
  ctx.fillText('LawGuard', 64, 100)

  ctx.fillStyle = '#14335c'
  ctx.font = `400 30px ${FONT_FAMILY}`
  ctx.fillText('刑事案件公益应急导航平台', 64, 150)

  // 帮助内容列表
  ctx.fillStyle = '#1f2937'
  ctx.font = `600 26px ${FONT_FAMILY}`
  ctx.fillText('帮助刑事案件当事人及家属了解：', 64, 250)

  ctx.font = `400 24px ${FONT_FAMILY}`
  ;['当前案件阶段', '一般性合法权利', '下一步行动', '官方救济渠道'].forEach((item, index) => {
    ctx.fillText(`· ${item}`, 64, 296 + index * 42)
  })

  // 信任信息（低饱和绿色，呼应 --color-success-text）
  ctx.fillStyle = '#1e6b3a'
  ctx.font = `600 24px ${FONT_FAMILY}`
  ;['纯公益', '永久免费', '不主动联系用户', '不收集个人信息'].forEach((item, index) => {
    ctx.fillText(`✓ ${item}`, 64, 470 + index * 36)
  })

  // 二维码（本地生成，不调用第三方在线接口）
  const qrDataUrl = await QRCode.toDataURL(shareUrl, { margin: 1, width: 190 })
  const qrImage = await loadImage(qrDataUrl)
  const qrSize = 190
  ctx.drawImage(qrImage, WIDTH - 64 - qrSize, HEIGHT - 64 - qrSize, qrSize, qrSize)

  // 底部网址
  ctx.fillStyle = '#5b6b7f'
  ctx.font = `400 20px ${FONT_FAMILY}`
  ctx.fillText(shareUrl, 64, HEIGHT - 40)

  return canvas.toDataURL('image/png')
}
