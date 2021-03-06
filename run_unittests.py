

__author__ = 'mjp, Oct 2016'
__license__ = 'Apache 2.0'


import unittest
import numpy as np

from data_tools import pixelwise_one_hot, tile_generator

import cnn_tools as ct
from cnn_tools import f1_score, pixelwise_ace_loss

import theano



class TestStuff(unittest.TestCase):
    
    def test_tile_generator(self):
        n = 10
        xa = np.ones((n,n))
        xb = 2*np.ones((n,n))
        xc = 3*np.ones((n,n))
        xd = 4*np.ones((n,n))

        xab = np.concatenate((xa,xb), axis=1)
        xcd = np.concatenate((xc,xd), axis=1)
        x = np.concatenate((xab,xcd), axis=0)

        gen = tile_generator(x, [n,n])
        pieces = [x[0] for x in gen]

        assert(len(pieces) == 4)
        assert(np.all(pieces[0] == xa))
        assert(np.all(pieces[1] == xb))
        assert(np.all(pieces[2] == xc))
        assert(np.all(pieces[3] == xd))

        gen = tile_generator(x, [n,n], stride=int(n/2))
        pieces = [x[0] for x in gen]
        
        assert(len(pieces) == 16)
        
        gen = tile_generator(x, [n,n], offset=n)
        pieces = [x[0] for x in gen]
        assert(len(pieces) == 1)
        assert(np.all(pieces[0] == xd))

        
    
    def test_f1_score(self):
        n_examples = 100
        n_classes = 2
        m,n = 16, 16    # num pixels
        n2 = np.floor(n/2).astype(np.int32)
        n4 = np.floor(n/4).astype(np.int32)

        y_true = np.zeros((n_examples, 1, m, n))
        y_true[:,:,:,0:n2] = 1
        y_true = pixelwise_one_hot(y_true, n_classes).astype(np.float32)

        # Note: we assume a theano backend here
        a = theano.tensor.tensor4('y_true')
        b = theano.tensor.tensor4('y_hat')
        f_theano = f1_score(a,b)
        
        result = f_theano.eval({a : y_true, b : y_true})
        self.assertTrue(np.abs(result - 1.0) < 1e-12)

        # case where all estimates are incorrect
        y_totally_wrong = 1 - y_true
        result = f_theano.eval({a : y_true, b : 1.0 - y_true})
        self.assertTrue(np.abs(result - 0.0) < 1e-12)

        # kill recall performance by 1/2
        y_recall_half = np.copy(y_true)
        y_recall_half[:,:,:,0:n4] =  1 - y_recall_half[:,:,:,0:n4]
        expected = 2./3      # 2 * (.5 * 1) / (.5 + 1)
        result = f_theano.eval({a : y_true, b : y_recall_half})
        self.assertTrue(np.abs(result - expected) < 1e-5)


        
    def test_y_onehot(self):
        n_classes = 10
        y_fake = np.random.randint(low=0, high=n_classes, size=(5,1,3,3))
        y_onehot = pixelwise_one_hot(y_fake, n_classes)
 
        self.assertTrue(y_onehot.shape[1] == 10)

        for kk in range(y_fake.shape[0]):
            for ii in range(y_fake.shape[2]):
                for jj in range(y_fake.shape[3]):
                    yi = y_fake[kk,0,ii,jj]
                    self.assertTrue(y_onehot[kk,yi,ii,jj])
                    self.assertTrue(np.sum(y_onehot[kk,:,ii,jj]) == 1)

        # make sure missing labels work as expected
        y_fake = np.random.randint(low=0, high=n_classes, size=(5,1,3,3))
        y_fake[0,:,:,:] = -10
        y_onehot = pixelwise_one_hot(y_fake, n_classes)
        assert(np.all(y_onehot[0,:,:,:] == 0))

        
    def test_pixelwise_ace_loss(self):
        n_examples = 100
        n_classes = 5
        m,n = 16, 16    # num pixels
        n2 = np.floor(n/2).astype(np.int32)
        n4 = np.floor(n/4).astype(np.int32)

        y_true_raw = np.random.randint(low=0, high=n_classes, size=(n_examples, 1, m, n))
        y_true = pixelwise_one_hot(y_true_raw, n_classes).astype(np.float32)

        # Note: we assume theano backend here
        a = theano.tensor.tensor4('y_true')
        b = theano.tensor.tensor4('y_hat')
        f_theano = pixelwise_ace_loss(a,b)

        #--------------------------------------------------
        # perfect estimate 
        #--------------------------------------------------
        lossPerfect = f_theano.eval({a : y_true, b : y_true})
        self.assertTrue(-1e-12 <= lossPerfect)  # the loss is generally non-negative

        lossTrivial = f_theano.eval({a : y_true, b : np.zeros(y_true.shape, dtype=np.float32)})
        self.assertTrue(lossPerfect < lossTrivial) 

        #--------------------------------------------------
        # If there are no class labels whatsoever, 1/N_labeled = inf
        #--------------------------------------------------
        lossNL = f_theano.eval({a : np.zeros(y_true.shape, dtype=np.float32), b : y_true})
        self.assertTrue(not np.isfinite(lossNL))

        #--------------------------------------------------
        # here we test to see that an error is worse from
        # a loss perspective than an unlabeled pixel.
        #--------------------------------------------------
        supp = np.random.randint(low=0, high=y_true_raw.size, size=(500,))
        y_true_u = np.copy(y_true_raw).flatten()
        y_true_u[supp] = -1

        y_hat = np.copy(y_true_u).flatten()
        y_hat[supp] = np.mod(y_true_u[supp] + 1, n_classes)  # all in error
        
        y_true_u = np.reshape(y_true_u, y_true_raw.shape)
        y_hat = np.reshape(y_hat, y_true_u.shape)
        
        y_true_u = pixelwise_one_hot(y_true_u, n_classes).astype(np.float32)
        y_hat = pixelwise_one_hot(y_hat, n_classes).astype(np.float32)
        
        loss1 = f_theano.eval({a : y_true, b : y_hat})
        loss2 = f_theano.eval({a : y_true_u, b : y_hat})
        self.assertTrue(loss2 < loss1)
        
        #--------------------------------------------------
        # test weighted losses
        #--------------------------------------------------
        y_binary = np.ones((1,1,32,32))
        y_binary_oh = pixelwise_one_hot(y_binary, 2).astype(np.float32)
        y_allwrong_oh = pixelwise_one_hot(0*y_binary, 2).astype(np.float32)
        
        f_theano = pixelwise_ace_loss(a,b,w=np.array([1,1]))
        loss0 = f_theano.eval({a : y_binary_oh, b : y_binary_oh})
        self.assertTrue(loss0 == 0)
        
        lossAllWrong = f_theano.eval({a : y_binary_oh, b : y_allwrong_oh})
        self.assertTrue(lossAllWrong > 0)
        
        f_theano = pixelwise_ace_loss(a,b,w=np.array([1,0]))
        lossAllWrong_0 = f_theano.eval({a : y_binary_oh, b : y_allwrong_oh})
        self.assertTrue(lossAllWrong_0 == 0)
        
        f_theano = pixelwise_ace_loss(a,b,w=np.array([1,2]))
        lossAllWrong_2 = f_theano.eval({a : y_binary_oh, b : y_allwrong_oh})
        self.assertTrue(lossAllWrong_2 > lossAllWrong)
        


    def test_monotonic_losses(self):
        y_true = np.zeros((5, 1, 10, 10), dtype=np.float32)
        for ii in np.arange(y_true.shape[3]):
            y_true[:,:,:,ii] = np.arange(y_true.shape[2])

        y_true_oh = pixelwise_one_hot(y_true, 10).astype(np.float32)

        # Note: we assume theano backend here
        y = theano.tensor.tensor4('y_true')
        yh = theano.tensor.tensor4('y_hat')

        loss_mono_y_th = ct.monotonic_in_row_loss(y, yh)

        out = loss_mono_y_th.eval({y : y_true_oh, yh : y_true_oh})

        self.assertTrue(out == 0)

        # TODO: more tests here...


    def test_tv_loss(self):
        y_true = np.zeros((5, 1, 10, 10), dtype=np.float32)
        y_true_oh = pixelwise_one_hot(y_true, 10).astype(np.float32)
        
        y = theano.tensor.tensor4('y_true')
        yh = theano.tensor.tensor4('y_hat')
        
        tv_loss = ct.total_variation_loss(y, yh)
        
        out = tv_loss.eval({y : y_true_oh, yh : y_true_oh})
        self.assertTrue(out == 0)

        # add some variability
        y_hat_oh = np.copy(y_true_oh)
        y_hat_oh[0,:,0,0] = 1
        out = tv_loss.eval({y : y_true_oh, yh : y_hat_oh})
        self.assertTrue(out > 0)
        
        
    def test_composite_loss(self):
        y_true_raw = np.random.randint(low=0, high=10, size=(100, 1, 32, 32))
        y_true_oh = pixelwise_one_hot(y_true_raw, 10).astype(np.float32)
        
        # Note: we assume theano backend here
        y = theano.tensor.tensor4('y_true')
        yh = theano.tensor.tensor4('y_hat')

        # These two should be equivalent, obviously
        loss_ace_th = ct.pixelwise_ace_loss(y, yh)
        loss_2 = ct.make_composite_loss(y, yh, ct.pixelwise_ace_loss, ct.pixelwise_ace_loss, 0.5, 0.5)

        print(loss_2)

        for ii in range(10):
            if ii > 0:
                y_hat_oh = np.random.randint(low=0, high=1, size=y_true_oh.shape).astype(np.float32)
            else:
                y_hat_oh = y_true_oh
                
            loss_a = loss_ace_th.eval({y : y_true_oh, yh : y_hat_oh})
            loss_b = loss_2.eval({y : y_true_oh, yh : y_hat_oh})
            
            self.assertTrue(np.abs(loss_a - loss_b) < 1e-3)

            
        # of course, the intent is to combine different loss functions
        # this next bit just makes sure the code doesn't crash (doesn't check correctness of result)
        loss_2b = ct.make_composite_loss(y, yh, ct.pixelwise_ace_loss, ct.monotonic_in_row_loss, 0.5, 0.5)
        foo = loss_2b.eval({y : y_true_oh, yh : y_hat_oh})


if __name__ == '__main__':
    unittest.main()
