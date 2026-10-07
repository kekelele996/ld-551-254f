<template>
  <el-tree
    class="chapter-tree"
    :data="treeData"
    node-key="key"
    default-expand-all
    :draggable="draggable"
    :allow-drop="allowDrop"
    @node-click="handleClick"
  >
    <template #default="{ data }">
      <span class="tree-node">
        <span class="node-label">
          <span v-if="data.lesson && getState(data.lesson.id, data.lesson.type) === 'passed'" class="state passed" title="已完成">✅</span>
          <span v-else-if="data.lesson && getState(data.lesson.id, data.lesson.type) === 'failed'" class="state failed" title="测验未及格（不计入已完成）">❌</span>
          <span>{{ data.label }}</span>
        </span>
        <span class="node-tags">
          <el-tag v-if="data.lesson && getState(data.lesson.id, data.lesson.type) === 'failed'" size="small" type="danger">未及格</el-tag>
          <el-tag v-else-if="data.lesson && data.lesson.type === LessonType.QUIZ && getState(data.lesson.id, data.lesson.type) === 'passed'" size="small" type="success">{{ getBest(data.lesson.id) }} 分</el-tag>
          <el-tag v-if="data.lesson?.is_free" size="small">试看</el-tag>
        </span>
      </span>
    </template>
  </el-tree>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { LessonType } from '@/constants/enums'
import type { Chapter } from '@/types/chapter'
import type { Lesson } from '@/types/lesson'
import type { LessonProgressItem } from '@/types/enrollment'

const props = withDefaults(
  defineProps<{
    chapters: Chapter[]
    lessonProgress?: LessonProgressItem[]
    draggable?: boolean
  }>(),
  { lessonProgress: () => [], draggable: true }
)
const emit = defineEmits<{ selectLesson: [lesson: Lesson] }>()

const progressById = computed(() => {
  const map = new Map<number, LessonProgressItem>()
  for (const item of props.lessonProgress) map.set(item.lesson_id, item)
  return map
})

function getState(lessonId: number, lessonType?: LessonType): 'passed' | 'failed' | undefined {
  const item = progressById.value.get(lessonId)
  if (!item) return undefined
  if (item.passed) return 'passed'
  // 已作答但未达及格线的测验，标红但不计入已完成；视频/文本不存在半完成态
  if (lessonType === LessonType.QUIZ && item.best_score !== null) return 'failed'
  return undefined
}

function getBest(lessonId: number): number | null {
  return progressById.value.get(lessonId)?.best_score ?? null
}

const treeData = computed(() =>
  props.chapters.map((chapter) => ({
    key: `chapter-${chapter.id}`,
    label: `${chapter.sort_order}. ${chapter.title}`,
    children: chapter.lessons.map((lesson) => ({
      key: `lesson-${lesson.id}`,
      label: `${lesson.sort_order}. ${lesson.title} · ${lesson.duration}分钟`,
      lesson
    }))
  }))
)

function allowDrop() {
  return props.draggable
}

function handleClick(data: { lesson?: Lesson }) {
  if (data.lesson) emit('selectLesson', data.lesson)
}
</script>

<style scoped>
.chapter-tree {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 8px;
}

.tree-node {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.node-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.node-tags {
  display: inline-flex;
  gap: 4px;
}

.state.failed {
  filter: none;
}
</style>
