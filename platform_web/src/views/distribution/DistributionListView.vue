<template>
  <div class="distribution-list-view">
    <h2 class="page-title">分发记录</h2>

    <div class="card">
      <div class="toolbar flex-between mb-md">
        <div class="toolbar-left flex gap-md">
          <el-select v-model="searchStatus" placeholder="发布状态" clearable style="width: 140px;">
            <el-option label="已分发" value="distributed" />
            <el-option label="待发布" value="pending_publish" />
            <el-option label="已发布" value="published" />
          </el-select>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
          <el-input
            v-model="searchKeyword"
            placeholder="搜索创作者/内容"
            :prefix-icon="Search"
            clearable
            style="width: 240px;"
          />
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
        </div>
      </div>

      <el-table :data="records" style="width: 100%">
        <el-table-column prop="id" label="记录ID" width="80" />
        <el-table-column prop="taskId" label="任务ID" width="80" />
        <el-table-column prop="contentTitle" label="内容标题" show-overflow-tooltip />
        <el-table-column prop="subUserName" label="创作者" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ row.statusLabel }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="distributedAt" label="分发时间" width="170" />
        <el-table-column prop="confirmedAt" label="确认发布时间" width="170" />
        <el-table-column label="操作" min-width="200">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewDetail(row)">预览</el-button>
            <el-button type="success" link size="small" v-if="row.status === 'distributed'">重新分发</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination mt-lg flex-between">
        <span class="total-text">共 {{ total }} 条记录</span>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
        />
      </div>
    </div>

    <el-dialog v-model="showPreview" title="内容详情" width="600px">
      <div class="content-detail">
        <h4 class="detail-title">{{ previewItem?.contentTitle }}</h4>
        <div class="detail-info">
          <p><span class="label">创作者:</span> {{ previewItem?.subUserName }}</p>
          <p><span class="label">分发时间:</span> {{ previewItem?.distributedAt }}</p>
          <p><span class="label">状态:</span>
            <el-tag :type="getStatusType(previewItem?.status)" size="small">
              {{ previewItem?.statusLabel }}
            </el-tag>
          </p>
        </div>
        <el-divider />
        <div class="detail-content">
          <h5>内容正文</h5>
          <p>{{ previewItem?.content }}</p>
        </div>
        <div class="detail-images mt-md" v-if="previewItem?.images?.length">
          <h5>配图</h5>
          <div class="image-list flex gap-md">
            <el-image
              v-for="(img, idx) in previewItem.images"
              :key="idx"
              :src="img"
              fit="cover"
              class="detail-image"
            />
          </div>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="copyContent">复制文案</el-button>
        <el-button type="success" @click="downloadImages">下载图片</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'

const searchKeyword = ref('')
const searchStatus = ref('')
const dateRange = ref()
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(120)
const showPreview = ref(false)
const previewItem = ref<any>(null)

const records = ref([
  {
    id: 'D001',
    taskId: 'T20240326002',
    contentTitle: '这款美妆产品真的超级好用！',
    subUserName: '小美同学',
    status: 'published',
    statusLabel: '已发布',
    distributedAt: '2024-03-26 15:00:00',
    confirmedAt: '2024-03-26 16:30:00',
    content: '这是生成的正文内容，包含了产品介绍、使用心得等...',
    images: ['', '']
  },
  {
    id: 'D002',
    taskId: 'T20240326002',
    contentTitle: '今日推荐：神仙水的正确打开方式',
    subUserName: '美妆博主',
    status: 'pending_publish',
    statusLabel: '待发布',
    distributedAt: '2024-03-26 15:05:00',
    confirmedAt: '',
    content: '这是生成的正文内容...',
    images: ['', '']
  },
  {
    id: 'D003',
    taskId: 'T20240325001',
    contentTitle: '母婴好物推荐',
    subUserName: '母婴达人',
    status: 'distributed',
    statusLabel: '已分发',
    distributedAt: '2024-03-25 18:00:00',
    confirmedAt: '',
    content: '这是生成的正文内容...',
    images: ['']
  }
])

const getStatusType = (status: string) => {
  const map: Record<string, any> = {
    distributed: 'info',
    pending_publish: 'warning',
    published: 'success'
  }
  return map[status] || 'info'
}

const handleSearch = () => {
  ElMessage.success('搜索功能触发')
}

const viewDetail = (row: any) => {
  previewItem.value = row
  showPreview.value = true
}

const copyContent = () => {
  ElMessage.success('文案已复制到剪贴板')
}

const downloadImages = () => {
  ElMessage.success('图片下载已开始')
}
</script>

<style lang="scss" scoped>
@import './distribution.scss';

.distribution-list-view {
  padding: 0;
}

.toolbar {
  margin-bottom: 16px;
}

.gap-md {
  gap: 12px;
}

.flex {
  display: flex;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.mb-md {
  margin-bottom: 16px;
}

.mt-md {
  margin-top: 16px;
}

.mt-lg {
  margin-top: 24px;
}

.pagination {
  padding: $spacing-sm 0;
  margin-top: $spacing-md;
  white-space: nowrap;
  display: flex;
  align-items: center;
}

.total-text {
  color: var(--color-text-secondary);
  font-size: $font-size-sm;
  white-space: nowrap;
  font-size: 14px;
  white-space: nowrap;
}

.content-detail {
  .detail-title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 16px;
  }
  .detail-info {
    p {
      margin-bottom: 8px;
      .label {
        color: #909399;
        margin-right: 8px;
      }
    }
  }
  .detail-content {
    h5 {
      font-size: 14px;
      font-weight: 500;
      margin-bottom: 8px;
    }
    p {
      color: #606266;
      line-height: 1.8;
    }
  }
  .detail-images {
    h5 {
      font-size: 14px;
      font-weight: 500;
      margin-bottom: 8px;
    }
    .image-list {
      .detail-image {
        width: 120px;
        height: 120px;
        border-radius: 4px;
        background: #f5f7fa;
      }
    }
  }
}
</style>
