<template>
  <div class="trend-analysis-panel">
    <!-- 筛选工具栏 -->
    <div class="filter-toolbar">
      <el-row :gutter="16" align="middle">
        <el-col :span="6">
          <span class="filter-label">时间范围</span>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            size="small"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 240px"
            @change="handleDateRangeChange"
          />
        </el-col>
        <el-col v-if="!isSubUser" :span="4">
          <span class="filter-label">时间维度</span>
          <el-select v-model="dimension" size="small" style="width: 100px" @change="handleDimensionChange">
            <el-option label="按天" value="day" />
            <el-option label="按周" value="week" />
            <el-option label="按月" value="month" />
          </el-select>
        </el-col>
        <el-col v-if="!isSubUser" :span="4">
          <span class="filter-label">对比类型</span>
          <el-select v-model="compareType" size="small" style="width: 100px" @change="handleCompareTypeChange">
            <el-option label="无对比" value="none" />
            <el-option label="环比" value="chain" />
            <el-option label="同比" value="year" />
          </el-select>
        </el-col>
        <el-col v-if="isSuperAdmin" :span="4">
          <span class="filter-label">管理员</span>
          <el-select
            v-model="selectedOperatorId"
            placeholder="全部管理员"
            clearable
            size="small"
            style="width: 120px"
            @change="handleOperatorChange"
          >
            <el-option
              v-for="op in operatorList"
              :key="op.id"
              :label="op.name"
              :value="op.id"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" size="small" :loading="loading" @click="loadAllData">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 内容发布趋势图表（所有角色统一展示） -->
    <el-row :gutter="20" class="mt-lg">
      <el-col :span="24">
        <div class="card">
          <div class="card-header">
            <h3 class="section-title">{{ isSubUser ? '我的内容发布趋势' : '内容发布趋势' }}</h3>
            <div class="trend-summary" v-if="publishTrend.total_generated">
              <span class="summary-item">
                {{ isSubUser ? '接收' : '生成' }}: <strong>{{ publishTrend.total_generated }}</strong>
              </span>
              <span class="summary-item">发布: <strong>{{ publishTrend.total_published }}</strong></span>
              <span class="summary-item">成功率: <strong>{{ publishTrend.success_rate }}%</strong></span>
              <span class="summary-item" v-if="publishTrend.generated_compare && !isSubUser">
                <span :class="getChangeClass(publishTrend.generated_compare.change_rate)">
                  {{ formatChangeRate(publishTrend.generated_compare.change_rate) }}
                </span>
              </span>
            </div>
          </div>
          <div ref="publishChartRef" class="chart-container-wide">
            <div v-show="loading" class="chart-loading-overlay">
              <el-icon class="loading-spinner"><Loading /></el-icon>
              <span>加载中...</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import {
  Refresh,
  Loading
} from '@element-plus/icons-vue'
import { apiClient, type OperatorOption, type PublishTrendResponse } from '@/api/types'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'

const authStore = useAuthStore()
const themeStore = useThemeStore()
const isSuperAdmin = computed(() => authStore.userRole === 'super_admin')
const isSubUser = computed(() => authStore.userRole === 'sub_user')

const getEChartsTheme = () => {
  return themeStore.mode === 'dark' ? 'dark' : undefined
}

const publishChartRef = ref<HTMLElement>()
let publishChart: echarts.ECharts | null = null

const dateRange = ref<[string, string] | null>(null)
const dimension = ref<'day' | 'week' | 'month'>('day')
const compareType = ref<'none' | 'chain' | 'year'>('none')
const selectedOperatorId = ref<number | undefined>(undefined)
const operatorList = ref<OperatorOption[]>([])

const loading = ref(true)

const publishTrend = ref<PublishTrendResponse>({
  data: [],
  total_generated: 0,
  total_published: 0,
  success_rate: 0,
  generated_compare: undefined,
  published_compare: undefined
})

const DEFAULT_DATE_RANGE_DAYS = 30

const getDefaultDateRange = (): [string, string] => {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - (DEFAULT_DATE_RANGE_DAYS - 1))
  return [
    start.toISOString().split('T')[0],
    end.toISOString().split('T')[0]
  ]
}

const loadFilterOptions = async () => {
  if (!isSuperAdmin.value) return
  try {
    const res = await apiClient.getTrendAnalysisFilterOptions()
    if (res) {
      operatorList.value = res.operators || []
    }
  } catch (error) {
    console.error('加载筛选选项失败:', error)
  }
}

const loadPublishTrend = async () => {
  try {
    const params: any = {
      dimension: dimension.value,
      compare_type: compareType.value
    }
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    if (selectedOperatorId.value) {
      params.operator_id = selectedOperatorId.value
    }
    const res = await apiClient.getPublishTrend(params)
    if (res) {
      publishTrend.value = res
      if (publishChart) {
        updatePublishChart()
      }
    }
  } catch (error: any) {
    console.error('加载发布趋势失败:', error)
    ElMessage.error('加载发布趋势失败')
  }
}

const loadAllData = async () => {
  try {
    loading.value = true
    await loadPublishTrend()
  } finally {
    loading.value = false
  }
}

const formatDateLabel = (dateStr: string) => {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}-${date.getDate()}`
}

const updatePublishChart = () => {
  if (!publishTrend.value.data?.length || !publishChart) return

  const data = publishTrend.value.data
  const dates = data.map((item: any) => {
    if (dimension.value === 'month') {
      return item.date
    } else if (dimension.value === 'week') {
      return item.date
    }
    return formatDateLabel(item.date)
  })

  const isDark = themeStore.mode === 'dark'
  const textColor = isDark ? '#e5e5e5' : '#303133'
  const lineColor = isDark ? '#424242' : '#e0e0e0'

  const generatedLabel = isSubUser.value ? '接收数量' : '生成数量'

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDark ? '#1f1f1f' : '#fff',
      textStyle: {
        color: textColor
      },
      formatter: (params: any) => {
        const dateInfo = params[0].axisValue
        let result = `${dateInfo}<br/>`
        params.forEach((item: any) => {
          if (item.seriesName === '成功率') {
            result += `${item.marker}${item.seriesName}: ${item.value}%<br/>`
          } else {
            result += `${item.marker}${item.seriesName}: ${item.value}<br/>`
          }
        })
        return result
      }
    },
    legend: {
      data: [generatedLabel, '发布数量', '成功率'],
      textStyle: {
        color: textColor
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLine: {
        lineStyle: {
          color: lineColor
        }
      },
      axisLabel: {
        color: textColor
      },
      splitLine: {
        lineStyle: {
          color: lineColor
        }
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '数量',
        position: 'left',
        axisLine: {
          lineStyle: {
            color: lineColor
          }
        },
        axisLabel: {
          color: textColor
        },
        splitLine: {
          lineStyle: {
            color: lineColor
          }
        }
      },
      {
        type: 'value',
        name: '成功率(%)',
        position: 'right',
        min: 0,
        max: 100,
        axisLine: {
          lineStyle: {
            color: lineColor
          }
        },
        axisLabel: {
          color: textColor,
          formatter: '{value}%'
        },
        splitLine: {
          show: false
        }
      }
    ],
    series: [
      {
        name: generatedLabel,
        type: 'line',
        smooth: true,
        data: data.map((item: any) => item.generated),
        itemStyle: { color: '#8B7CF6' }, // 柔和紫主题色
        areaStyle: { color: 'rgba(139, 124, 246, 0.1)' }
      },
      {
        name: '发布数量',
        type: 'line',
        smooth: true,
        data: data.map((item: any) => item.published),
        itemStyle: { color: '#34C759' } // 苹果绿
      },
      {
        name: '成功率',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: data.map((item: any) => item.success_rate),
        itemStyle: { color: '#FF9500' }, // 苹果橙
        lineStyle: { type: 'dashed' }
      }
    ]
  }
  publishChart.setOption(option)
}

const initCharts = async () => {
  await nextTick()

  const theme = getEChartsTheme()

  if (publishChartRef.value) {
    publishChart = echarts.init(publishChartRef.value, theme)
  }

  window.addEventListener('resize', handleResize)
}

const reinitChartsForTheme = async () => {
  const hasData = publishTrend.value.data?.length > 0

  publishChart?.dispose()

  await initCharts()
  if (hasData) {
    updatePublishChart()
  }
}

watch(() => themeStore.mode, () => {
  reinitChartsForTheme()
})

const handleResize = () => {
  publishChart?.resize()
}

const getChangeClass = (changeRate: number) => {
  if (changeRate > 0) return 'change-up'
  if (changeRate < 0) return 'change-down'
  return 'change-zero'
}

const formatChangeRate = (changeRate: number) => {
  const prefix = changeRate > 0 ? '+' : ''
  return `${prefix}${changeRate.toFixed(1)}%`
}

const handleDateRangeChange = () => {
  loadAllData()
}

const handleDimensionChange = () => {
  loadAllData()
}

const handleCompareTypeChange = () => {
  loadAllData()
}

const handleOperatorChange = () => {
  loadAllData()
}

onMounted(async () => {
  dateRange.value = getDefaultDateRange()
  await nextTick()
  await initCharts()
  await loadFilterOptions()
  await loadAllData()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  publishChart?.dispose()
})

</script>

<style lang="scss" scoped>
.trend-analysis-panel {
  padding: 0;
}

.filter-toolbar {
  background: var(--bg-secondary);
  border-radius: 8px;
  box-shadow: var(--shadow-md);
  padding: 16px 20px;
  margin-bottom: 20px;
}

.filter-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-right: 8px;
}

.card {
  background: var(--bg-secondary);
  border-radius: 8px;
  box-shadow: var(--shadow-md);
  padding: 20px;
  height: 100%;
}

.card-header {
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  margin: 0;
  color: var(--text-primary);
}

.trend-summary {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: var(--text-secondary);
}

.summary-item {
  strong {
    color: var(--text-primary);
    font-weight: 600;
  }
}

.change-up {
  color: #67C23A;
  font-weight: 600;
}

.change-down {
  color: #F56C6C;
  font-weight: 600;
}

.change-zero {
  color: var(--text-placeholder);
}

.chart-container {
  width: 100%;
  height: 300px;
  position: relative;
}

.chart-container-wide {
  width: 100%;
  height: 350px;
  position: relative;
}

.chart-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
  background: var(--bg-tertiary);
  opacity: 0.95;
  border-radius: 8px;
  z-index: 10;
}

.loading-spinner {
  animation: loading-rotate 1s linear infinite;
}

@keyframes loading-rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.mt-lg {
  margin-top: 20px;
}
</style>