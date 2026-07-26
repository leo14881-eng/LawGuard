/**
 * 官方求助渠道 · 省级查询骨架数据（对应 LAWGUARD_SOT.md BL-002）。
 *
 * 重要限制（P0.2 / BL-002）：各省具体机构名称、电话、地址目前没有可核验的官方
 * 来源，本文件不得填入任何具体机构名称、电话或地址，一律使用统一占位文案，
 * 核验状态固定为 pending（待官方链接核验）。待人工提供可核验官方来源后，
 * 再由人工更新对应条目并解除 BLOCKED，不得由自动开发流程自行编造或推断。
 *
 * 全国性渠道（12348 公共法律服务热线 / 12309 检察服务中心）已在
 * OfficialChannelsView.vue 中单独维护，本文件不重复收录，避免出现两处数据源。
 */

/** 省级查询条目的核验状态：当前骨架阶段仅使用 pending，verified 预留给未来人工核验通过后的数据 */
export type ProvinceChannelVerificationStatus = 'pending' | 'verified'

/** 单个省级行政区的官方求助渠道占位条目 */
export interface ProvinceChannelEntry {
  /** 省级行政区编码，用于筛选控件的 value 与列表 key，取拼音首字母缩写 */
  code: string
  /** 省级行政区名称，例如"北京市""广东省" */
  province: string
  /** 机构名称；未核验前固定为占位文案，不得填入具体机构名 */
  name: string
  /** 联系方式；未核验前固定为占位文案，不得填入具体电话或地址 */
  contact: string
  /** 核验状态，骨架阶段全部为 pending */
  verificationStatus: ProvinceChannelVerificationStatus
}

/** 中国大陆 31 个省级行政区名称（不含港澳台，V1 暂不涉及） */
const PROVINCE_NAMES: Array<{ code: string; province: string }> = [
  { code: 'BJ', province: '北京市' },
  { code: 'TJ', province: '天津市' },
  { code: 'HE', province: '河北省' },
  { code: 'SX', province: '山西省' },
  { code: 'NM', province: '内蒙古自治区' },
  { code: 'LN', province: '辽宁省' },
  { code: 'JL', province: '吉林省' },
  { code: 'HL', province: '黑龙江省' },
  { code: 'SH', province: '上海市' },
  { code: 'JS', province: '江苏省' },
  { code: 'ZJ', province: '浙江省' },
  { code: 'AH', province: '安徽省' },
  { code: 'FJ', province: '福建省' },
  { code: 'JX', province: '江西省' },
  { code: 'SD', province: '山东省' },
  { code: 'HA', province: '河南省' },
  { code: 'HB', province: '湖北省' },
  { code: 'HN', province: '湖南省' },
  { code: 'GD', province: '广东省' },
  { code: 'GX', province: '广西壮族自治区' },
  { code: 'HI', province: '海南省' },
  { code: 'CQ', province: '重庆市' },
  { code: 'SC', province: '四川省' },
  { code: 'GZ', province: '贵州省' },
  { code: 'YN', province: '云南省' },
  { code: 'XZ', province: '西藏自治区' },
  { code: 'SN', province: '陕西省' },
  { code: 'GS', province: '甘肃省' },
  { code: 'QH', province: '青海省' },
  { code: 'NX', province: '宁夏回族自治区' },
  { code: 'XJ', province: '新疆维吾尔自治区' },
]

/** 未核验条目统一占位文案，避免任何形式的具体机构信息被误当作正式内容展示 */
const PLACEHOLDER_NAME = '具体机构名称待核验'
const PLACEHOLDER_CONTACT = '具体联系方式待核验，可先拨打 12348 或 12309 转接咨询'

/** 省级官方求助渠道占位列表，骨架阶段全部条目核验状态为 pending */
export const officialChannelsByProvince: ProvinceChannelEntry[] = PROVINCE_NAMES.map(
  ({ code, province }) => ({
    code,
    province,
    name: PLACEHOLDER_NAME,
    contact: PLACEHOLDER_CONTACT,
    verificationStatus: 'pending',
  })
)
