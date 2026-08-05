import { describe, expect, it } from 'vitest'
import {
  clampToAllowedView,
  filterNavItems,
  getWorkspaceDefinition,
} from './registry'

describe('workspace registry', () => {
  it('includes Seller workspace capabilities for ecommerce spaces', () => {
    const def = getWorkspaceDefinition('ecommerce')
    const keys = def.navItems.map((item) => item.key)

    expect(def.defaultView).toBe('workbench')
    expect(def.capabilities).toEqual(
      expect.arrayContaining(['workbench', 'products', 'stock', 'movements', 'summary', 'seller-ai']),
    )
    expect(keys).toEqual(
      expect.arrayContaining(['overview', 'resources', 'workbench', 'products', 'stock', 'seller-ai']),
    )
    expect(def.navItems.find((item) => item.key === 'resources')?.section).toBe('resources')
    expect(def.navItems.find((item) => item.key === 'seller-ai')?.component).toBeTruthy()
  })

  it('excludes Seller capabilities and space leave from personal spaces', () => {
    const def = getWorkspaceDefinition('personal')
    const keys = def.navItems.map((item) => item.key)

    expect(def.defaultView).toBe('overview')
    expect(keys).toEqual(
      expect.arrayContaining(['overview', 'resources', 'persons', 'timeline', 'flows', 'space-create', 'space-join']),
    )
    expect(keys).not.toContain('seller-ai')
    expect(keys).not.toContain('stock')
    expect(keys).not.toContain('space-leave')
    expect(keys).not.toContain('space-review')
  })

  it('uses generic observation capabilities for non-ecommerce spaces', () => {
    for (const orgType of ['campaign', 'family', 'starship', 'company']) {
      const def = getWorkspaceDefinition(orgType)
      const keys = def.navItems.map((item) => item.key)

      expect(def.defaultView).toBe('overview')
      expect(keys).toEqual(
        expect.arrayContaining(['overview', 'resources', 'persons', 'timeline', 'flows']),
      )
      expect(keys).toContain('space-leave')
      expect(keys).not.toContain('seller-ai')
    }
  })

  it('filters role-protected nav items with the current role only', () => {
    const def = getWorkspaceDefinition('company')
    const memberKeys = filterNavItems(def.navItems, 'member').map((item) => item.key)
    const ownerKeys = filterNavItems(def.navItems, 'owner').map((item) => item.key)

    expect(memberKeys).not.toContain('space-manage')
    expect(memberKeys).not.toContain('space-review')
    expect(memberKeys).toContain('space-leave')
    expect(ownerKeys).toContain('space-manage')
    expect(ownerKeys).toContain('space-review')
  })

  it('clamps unknown, unsupported, and role-protected views to the default view', () => {
    const company = getWorkspaceDefinition('company')
    const personal = getWorkspaceDefinition('personal')

    expect(clampToAllowedView(undefined, company, 'owner')).toBe('overview')
    expect(clampToAllowedView('missing', company, 'owner')).toBe('overview')
    expect(clampToAllowedView('stock', company, 'owner')).toBe('overview')
    expect(clampToAllowedView('space-review', company, 'member')).toBe('overview')
    expect(clampToAllowedView('space-leave', personal, 'owner')).toBe('overview')
    expect(clampToAllowedView('space-review', company, 'owner')).toBe('space-review')
  })
})
