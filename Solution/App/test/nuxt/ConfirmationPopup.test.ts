import { describe, it, expect } from 'vitest';
import { mountSuspended } from '@nuxt/test-utils/runtime';
import ConfirmationPopup from '~/components/UI/ConfirmationPopup.vue';
import type { VueWrapper } from '@vue/test-utils';
import { nextTick } from 'vue';

const UModalStub = {
  name: 'UModal',
  props: ['title'],
  template: '<div><h1>{{ title }}</h1><slot name="body" /><slot name="footer" /></div>'
};

const UButtonStub = {
  name: 'UButton',
  props: ['label'],
  template: '<button>{{ label }}</button>'
};

describe('ConfirmationPopup.vue', () => {
  let wrapper: VueWrapper<any>;

  const mountComponent = async (props = {}) => {
    return await mountSuspended(ConfirmationPopup, {
      props,
      global: {
        stubs: {
          UModal: UModalStub,
          UButton: UButtonStub
        }
      }
    });
  };

  it('renders with default title', async () => {
    wrapper = await mountComponent();
    expect(wrapper.text()).toContain('Are you sure?');
  });

  it('renders with a custom title and description', async () => {
    wrapper = await mountComponent({
      title: 'Custom Title',
      description: 'Custom Description'
    });
    expect(wrapper.text()).toContain('Custom Title');
    expect(wrapper.text()).toContain('Custom Description');
  });

  it('emits close event with true when confirm is clicked', async () => {
    wrapper = await mountComponent({ confirmButton: 'Yes, do it' });
    const buttons = wrapper.findAll('button');
    const confirmButton = buttons.find((b) => b.text() === 'Yes, do it');
    expect(confirmButton).toBeTruthy();
    await confirmButton!.trigger('click');

    await nextTick();

    expect(wrapper.emitted('close')).toBeTruthy();
    expect(wrapper.emitted('close')![0]).toEqual([true]);
  });

  it('emits close event with false when cancel is clicked', async () => {
    wrapper = await mountComponent({ cancelButton: 'No, go back' });
    const buttons = wrapper.findAll('button');
    const cancelButton = buttons.find((b) => b.text() === 'No, go back');
    expect(cancelButton).toBeTruthy();
    await cancelButton!.trigger('click');

    await nextTick();

    expect(wrapper.emitted('close')).toBeTruthy();
    expect(wrapper.emitted('close')![0]).toEqual([false]);
  });

  it('does not render footer when actionsEnabled is false', async () => {
    wrapper = await mountComponent({
      actionsEnabled: false,
      confirmButton: 'Confirm',
      cancelButton: 'Cancel'
    });

    const buttons = wrapper.findAll('button');
    const confirmButton = buttons.find((b) => b.text() === 'Confirm');
    const cancelButton = buttons.find((b) => b.text() === 'Cancel');
    expect(confirmButton).toBeUndefined();
    expect(cancelButton).toBeUndefined();
  });
});
