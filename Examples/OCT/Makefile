# Train OCT CNNs
#
# mjp, may 2017

CC=python
#CC=THEANO_FLAGS="device=gpu1,floatX=float32" python 

train :
	$(CC) train_oct.py


# some very crude hyperparameter grid search
launch-fighters :
	THEANO_FLAGS="device=gpu1,floatX=float32" nohup python train_oct.py trial_A 10 1000 &
	sleep 5
	THEANO_FLAGS="device=gpu2,floatX=float32" nohup python train_oct.py trial_B 5 100 &
	sleep 5
	THEANO_FLAGS="device=gpu3,floatX=float32" nohup python train_oct.py trial_C 100 100 &
	sleep 5
	THEANO_FLAGS="device=gpu4,floatX=float32" nohup python train_oct.py trial_D 5 10 &
	sleep 5
	THEANO_FLAGS="device=gpu5,floatX=float32" nohup python train_oct.py trial_E 1 1000 &
	sleep 5
	THEANO_FLAGS="device=gpu6,floatX=float32" nohup python train_oct.py trial_F 20 1000 &

launch-fighters-2 :
	THEANO_FLAGS="device=gpu1,floatX=float32" nohup python train_oct.py hyper_001 20 800 &
	sleep 5
	THEANO_FLAGS="device=gpu2,floatX=float32" nohup python train_oct.py hyper_002 20 500 &
	sleep 5
	THEANO_FLAGS="device=gpu3,floatX=float32" nohup python train_oct.py hyper_003 20 250 &
	sleep 5
	THEANO_FLAGS="device=gpu4,floatX=float32" nohup python train_oct.py hyper_004 10 800 &
	sleep 5
	THEANO_FLAGS="device=gpu5,floatX=float32" nohup python train_oct.py hyper_005 10 500 &
	sleep 5
	THEANO_FLAGS="device=gpu6,floatX=float32" nohup python train_oct.py hyper_006 10 250 &


clean :
	\rm -f oct_segmentation_*.{npz,hdf5}
	\rm -f oct_detection_*.{npz,hdf5}
