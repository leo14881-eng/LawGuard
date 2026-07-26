/**
 * 手机号脱敏工具：打印/保存行动清单时默认使用，保留前 3 位与后 4 位，
 * 中间以 * 替换（例如 "13812345678" -> "138****5678"）。
 * 非常规长度或非数字输入原样返回中间打码，不尝试识别具体号码格式。
 */
export function maskPhone(phone: string): string {
  const digitsOnly = phone.replace(/\D/g, '')
  if (digitsOnly.length < 7) {
    return phone
  }
  const head = digitsOnly.slice(0, 3)
  const tail = digitsOnly.slice(-4)
  return `${head}****${tail}`
}
