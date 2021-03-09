# 安装说明
* TensorFlow 安装：请根据实验环境（CUDA版本、cudnn版本）选择合适的Tensorflow进行下载安装（TensorFlow版本大于2.0）。

* BigBird安装

```
git clone https://github.com/joey12300/bigbird.git
cd bigbird
git checkout test
pip3 install -e .
```

# 运行预训练脚本

```
cd bigbird/pretrain
python run_pretraining.py --learning_rate 1e-5 --num_train_steps 100000 --train_batch_size 4
```

重要参数如下：
* train_batch_size：训练批大小。默认是4。
* num_train_steps：训练轮次。默认100000。
* learning_rate：学习率。默认1e-4
* save_checkpoints_steps：checkpoint保存间隔，默认为1000。

主要比较loss曲线图，观察收敛效果。


# 运行分类脚本

```
cd bigbird/classifier/
python imdb.py --max_encoder_length 3072 --learning_rate 1e-5 --num_train_steps 10000 --train_batch_size 2 --eval_batch_size 2
```
假如无法下载预训练模型，可以通过以下方式操作：

```
mkdir -p bigbird/ckpt
gsutil cp -r gs://bigbird-transformer/pretrain/bigbr_base bigbird/ckpt/

添加参数init_checkpoint（最好指定绝对路径），执行脚本：
python imdb.py --max_encoder_length 3072 --learning_rate 1e-5 --num_train_steps 10000 --train_batch_size 2 --eval_batch_size 2 --init_checkpoint  bigbird/ckpt/bigbr_base/model.ckpt-0
```


重要参数如下：
* train_batch_size：训练批大小。默认是8。
* eval_batch_size: 评估批大小。默认为8.
* learning_rate：学习率。默认1e-5。
* save_checkpoints_steps：checkpoint保存间隔，默认为1000。
* num_train_steps：训练轮次。默认16000。

预期Acc：0.9458 （误差：正负0.004）
