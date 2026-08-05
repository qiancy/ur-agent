import type { Component } from 'vue'

export type WorkspaceCapability =
  | 'overview'
  | 'resources'
  | 'persons'
  | 'timeline'
  | 'flows'
  | 'products'
  | 'stock'
  | 'movements'
  | 'summary'
  | 'seller-ai'
  | 'workbench'
  | 'space-manage'
  | 'space-create'
  | 'space-join'
  | 'space-review'
  | 'space-leave'

export type WorkspaceNavGroup = 'observe' | 'operate' | 'ai' | 'governance'
export type WorkspaceNavKind = 'view' | 'action'
export type GenericSection = 'overview' | 'resources' | 'persons' | 'timeline' | 'flows'
export type WorkspaceViewComponent = Component | (() => Promise<Component>)

export interface WorkspaceNavItem {
  key: WorkspaceCapability
  label: string
  icon: string
  kind: WorkspaceNavKind
  group: WorkspaceNavGroup
  requiresRole?: Array<'owner' | 'admin' | 'member' | 'viewer'>
  component?: WorkspaceViewComponent
  section?: GenericSection
}

export interface WorkspaceDefinition {
  orgType: string
  defaultView: WorkspaceCapability
  capabilities: WorkspaceCapability[]
  navItems: WorkspaceNavItem[]
}
