import argparse

import chainer
from chainer import iterators

from chainercv.datasets import voc_bbox_label_names
from chainercv.datasets import VOCBboxDataset
from chainercv.evaluations import eval_detection_voc
from chainercv.links import FasterRCNNVGG16
from chainercv.links import SSD300
from chainercv.links import SSD512
from chainercv.utils import apply_prediction_to_iterator
from chainercv.utils import ProgressHook


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--model', choices=('faster_rcnn', 'ssd300', 'ssd512'),
        default='ssd300')
    parser.add_argument('--pretrained_model')
    parser.add_argument('--gpu', type=int, default=-1)
    parser.add_argument('--batchsize', type=int, default=32)
    args = parser.parse_args()

    if args.model == 'faster_rcnn':
        if args.pretrained_model:
            model = FasterRCNNVGG16(
                n_fg_class=20,
                pretrained_model=args.pretrained_model)
        else:
            model = FasterRCNNVGG16(pretrained_model='voc07')
    elif args.model == 'ssd300':
        if args.pretrained_model:
            model = SSD300(
                n_fg_class=20,
                pretrained_model=args.pretrained_model)
        else:
            model = SSD300(pretrained_model='voc0712')
    elif args.model == 'ssd512':
        if args.pretrained_model:
            model = SSD512(
                n_fg_class=20,
                pretrained_model=args.pretrained_model)
        else:
            model = SSD512(pretrained_model='voc0712')

    if args.gpu >= 0:
        chainer.cuda.get_device_from_id(args.gpu).use()
        model.to_gpu()

    model.use_preset('evaluate')

    dataset = VOCBboxDataset(
        year='2007', split='test', use_difficult=True, return_difficult=True)
    iterator = iterators.SerialIterator(
        dataset, args.batchsize, repeat=False, shuffle=False)

    imgs, pred_values, gt_values = apply_prediction_to_iterator(
        model.predict, iterator, hook=ProgressHook(len(dataset)))
    # delete unused iterator explicitly
    del imgs

    pred_bboxes, pred_labels, pred_scores = pred_values
    gt_bboxes, gt_labels, gt_difficults = gt_values

    result = eval_detection_voc(
        pred_bboxes, pred_labels, pred_scores,
        gt_bboxes, gt_labels, gt_difficults,
        use_07_metric=True)

    print()
    print('mAP: {:f}'.format(result['map']))
    for l, name in enumerate(voc_bbox_label_names):
        if result['ap'][l]:
            print('{:s}: {:f}'.format(name, result['ap'][l]))
        else:
            print('{:s}: -'.format(name))


if __name__ == '__main__':
    main()
