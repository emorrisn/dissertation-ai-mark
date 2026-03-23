import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mountSuspended } from '@nuxt/test-utils/runtime';
import type { VueWrapper } from '@vue/test-utils';
import DashboardMobileNav from '~/components/DashboardMobileNav.vue';

// Mock the router and route
const mockRouter = {
  push: vi.fn()
};
const mockRoute = {
  path: '/'
};
vi.mock('vue-router', async () => {
  const actual = await vi.importActual('vue-router');
  return {
    ...actual,
    useRouter: () => mockRouter,
    useRoute: () => mockRoute
  };
});

const UDashboardToolbarStub = {
  name: 'UDashboardToolbar',
  template: '<div data-testid="toolbar"><slot /></div>'
};

const IconStub = {
  name: 'Icon',
  props: ['name'],
  template: '<i :class="name"></i>'
};

const UButtonStub = {
  name: 'UButton',
  template: '<button @click="$emit(\'click\')"><slot /></button>'
};

describe('DashboardMobileNav.vue', () => {
  let wrapper: VueWrapper<any>;

  const mountComponent = async (path: string) => {
    mockRoute.path = path;
    return await mountSuspended(DashboardMobileNav, {
      global: {
        stubs: { UDashboardToolbar: UDashboardToolbarStub, Icon: IconStub, UButton: UButtonStub }
      }
    });
  };

  beforeEach(() => {
    mockRouter.push.mockClear();
  });

  it('does not render when route is not on a dashboard page', async () => {
    wrapper = await mountComponent('/');
    expect(wrapper.find('[data-testid="toolbar"]').exists()).toBe(false);
  });

  it('renders on /dashboard/updates page', async () => {
    wrapper = await mountComponent('/dashboard/updates');
    expect(wrapper.find('[data-testid="toolbar"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('Updates');
    expect(wrapper.text()).toContain('Sessions');
  });

  it('renders on /dashboard/marking page', async () => {
    wrapper = await mountComponent('/dashboard/marking');
    expect(wrapper.find('[data-testid="toolbar"]').exists()).toBe(true);
  });

  it('marks "Updates" as active on its page', async () => {
    wrapper = await mountComponent('/dashboard/updates');
    const updatesButton = wrapper.findAll('button').find((b) => b.text().includes('Updates'));
    expect(updatesButton?.attributes('aria-current')).toBe('page');
  });

  it('marks "Sessions" as active on its page', async () => {
    wrapper = await mountComponent('/dashboard/marking');
    const sessionsButton = wrapper.findAll('button').find((b) => b.text().includes('Sessions'));
    expect(sessionsButton?.attributes('aria-current')).toBe('page');
  });

  it('calls router.push when an inactive item is clicked', async () => {
    wrapper = await mountComponent('/dashboard/updates');
    const sessionsButton = wrapper.findAll('button').find((b) => b.text().includes('Sessions'));
    await sessionsButton!.trigger('click');
    expect(mockRouter.push).toHaveBeenCalledWith('/dashboard/marking');
  });

  it('does not call router.push when the active item is clicked', async () => {
    wrapper = await mountComponent('/dashboard/updates');
    const updatesButton = wrapper.findAll('button').find((b) => b.text().includes('Updates'));
    await updatesButton!.trigger('click');
    expect(mockRouter.push).not.toHaveBeenCalled();
  });
});
