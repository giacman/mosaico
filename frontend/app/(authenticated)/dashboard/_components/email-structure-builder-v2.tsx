"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Plus, GripVertical, X } from "lucide-react"
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

type ComponentType = "subject" | "pre_header" | "title" | "body" | "cta"

interface StructureComponent {
  component: ComponentType
  count: number
}

interface EmailStructureBuilderProps {
  value: StructureComponent[]
  onChange: (structure: StructureComponent[]) => void
}

interface DraggableItem {
  id: string
  type: ComponentType
}

function SortableItem({ id, type, onRemove }: { id: string; type: ComponentType; onRemove: () => void }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  const getLabel = (type: ComponentType) => {
    const labels = {
      subject: "Subject",
      pre_header: "Pre-header",
      title: "Title",
      body: "Body Section",
      cta: "CTA Button",
    }
    return labels[type]
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="flex items-center gap-3 rounded-lg border bg-card p-3 hover:bg-accent/50 transition-colors"
    >
      <div
        {...attributes}
        {...listeners}
        className="cursor-grab active:cursor-grabbing touch-none"
      >
        <GripVertical className="h-5 w-5 text-muted-foreground" />
      </div>
      <div className="flex-1">
        <span className="text-sm font-medium">{getLabel(type)}</span>
      </div>
      <Button
        variant="ghost"
        size="sm"
        onClick={onRemove}
        className="h-8 w-8 p-0"
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  )
}

export function EmailStructureBuilderV2({ value, onChange }: EmailStructureBuilderProps) {
  // Convert structure to flat list for drag-and-drop
  const [items, setItems] = useState<DraggableItem[]>(() => {
    const result: DraggableItem[] = []
    let idCounter = 0
    
    // Always include subject and pre_header first
    const hasSubject = value.some(s => s.component === 'subject')
    const hasPreHeader = value.some(s => s.component === 'pre_header')
    
    if (hasSubject) result.push({ id: `subject-${idCounter++}`, type: 'subject' })
    if (hasPreHeader) result.push({ id: `pre_header-${idCounter++}`, type: 'pre_header' })
    
    // Add other components
    value.forEach(s => {
      if (s.component !== 'subject' && s.component !== 'pre_header') {
        for (let i = 0; i < s.count; i++) {
          result.push({ id: `${s.component}-${idCounter++}`, type: s.component })
        }
      }
    })
    
    return result
  })

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    if (over && active.id !== over.id) {
      setItems((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id)
        const newIndex = items.findIndex((item) => item.id === over.id)
        
        // Don't allow moving subject or pre_header below other elements
        const isMovingFixed = items[oldIndex].type === 'subject' || items[oldIndex].type === 'pre_header'
        const targetItem = items[newIndex]
        const targetIsFixed = targetItem.type === 'subject' || targetItem.type === 'pre_header'
        
        if (isMovingFixed && newIndex > 1) return items
        if (!isMovingFixed && targetIsFixed) return items
        
        const newItems = arrayMove(items, oldIndex, newIndex)
        updateStructureFromItems(newItems)
        return newItems
      })
    }
  }

  const updateStructureFromItems = (items: DraggableItem[]) => {
    const componentCounts = new Map<ComponentType, number>()
    
    items.forEach(item => {
      componentCounts.set(item.type, (componentCounts.get(item.type) || 0) + 1)
    })
    
    const newStructure: StructureComponent[] = []
    componentCounts.forEach((count, component) => {
      newStructure.push({ component, count })
    })
    
    onChange(newStructure)
  }

  const addComponent = (type: ComponentType) => {
    const newId = `${type}-${Date.now()}`
    const newItems = [...items, { id: newId, type }]
    setItems(newItems)
    updateStructureFromItems(newItems)
  }

  const removeComponent = (id: string) => {
    const item = items.find(i => i.id === id)
    
    // Don't allow removing subject or pre_header
    if (item && (item.type === 'subject' || item.type === 'pre_header')) {
      return
    }
    
    const newItems = items.filter(i => i.id !== id)
    setItems(newItems)
    updateStructureFromItems(newItems)
  }

  // Ensure subject and pre_header are always present
  useEffect(() => {
    const hasSubject = items.some(i => i.type === 'subject')
    const hasPreHeader = items.some(i => i.type === 'pre_header')
    
    if (!hasSubject || !hasPreHeader) {
      let newItems = [...items]
      
      if (!hasSubject) {
        newItems = [{ id: `subject-${Date.now()}`, type: 'subject' as const }, ...newItems]
      }
      
      if (!hasPreHeader) {
        const subjectIndex = newItems.findIndex(i => i.type === 'subject')
        const insertIndex = subjectIndex >= 0 ? subjectIndex + 1 : 0
        newItems = [
          ...newItems.slice(0, insertIndex),
          { id: `pre_header-${Date.now()}`, type: 'pre_header' as const },
          ...newItems.slice(insertIndex)
        ]
      }
      
      setItems(newItems)
      updateStructureFromItems(newItems)
    }
  }, []) // Only run on mount

  return (
    <Card>
      <CardHeader>
        <CardTitle>Email Structure</CardTitle>
        <CardDescription>
          Subject and Pre-header are required. Drag to reorder Title, Body, and CTA components.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={items.map(i => i.id)}
            strategy={verticalListSortingStrategy}
          >
            <div className="space-y-2">
              {items.map((item) => (
                <SortableItem
                  key={item.id}
                  id={item.id}
                  type={item.type}
                  onRemove={() => removeComponent(item.id)}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>

        <div className="pt-4 border-t">
          <p className="text-sm font-medium mb-3">Add Components:</p>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => addComponent('title')}
              className="gap-2"
            >
              <Plus className="h-3.5 w-3.5" />
              Title
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => addComponent('body')}
              className="gap-2"
            >
              <Plus className="h-3.5 w-3.5" />
              Body Section
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => addComponent('cta')}
              className="gap-2"
            >
              <Plus className="h-3.5 w-3.5" />
              CTA Button
            </Button>
          </div>
        </div>

        <div className="pt-4 border-t">
          <p className="text-sm font-medium mb-2">Current Structure:</p>
          <div className="text-xs text-muted-foreground space-y-1">
            <p>Total Components: {items.length}</p>
            <div className="flex flex-wrap gap-2 mt-2">
              {items.map((item, index) => (
                <Badge key={item.id} variant="secondary" className="text-xs">
                  {index + 1}. {item.type.replace('_', ' ')}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

