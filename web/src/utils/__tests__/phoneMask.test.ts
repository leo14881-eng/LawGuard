import { describe, expect, it } from 'vitest'
import { maskPhone } from '../phoneMask'

describe('maskPhone：场景11 手机号默认脱敏', () => {
  it('11 位手机号脱敏为 138****5678 格式', () => {
    expect(maskPhone('13812345678')).toBe('138****5678')
  })

  it('带分隔符的号码先提取数字再脱敏', () => {
    expect(maskPhone('138-1234-5678')).toBe('138****5678')
  })

  it('过短或非号码内容原样返回，不误判', () => {
    expect(maskPhone('12345')).toBe('12345')
    expect(maskPhone('')).toBe('')
  })
})
