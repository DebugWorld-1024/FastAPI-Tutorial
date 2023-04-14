
import smtplib
from email.utils import formataddr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from library.initializer.log import Log
from library.constants import MailReceiver
from library.config.config import load_config


class MailClient(object):
    """
    Usage:
        >>> from library.initializer.mail_client import MailClient
        >>> sender = MailClient(receivers=['xxxx@Foxmail.com'])
        >>> sender.info('title', 'content')
        >>> MailClient().error(subject='title', content='content')
    """

    def __init__(self, mail_config: dict = load_config('app.alert_mail_config'),
                 receivers: list = MailReceiver.RECEIVERS, cc_receivers: list = None):
        """

        :param mail_config: 发件邮箱配置
        :param receivers: 收件人
        :param cc_receivers: 抄送人
        """
        self.mail_config = mail_config
        self.receivers = receivers
        self.cc_receivers = cc_receivers

    def __send_mail(self, subject: str, content: str, subtype: str = 'html', charset: str = 'utf-8',
                    filepath: str = None, filename: str = None, level: str = ''):
        """

        :param subject: 邮件标题
        :param content: 邮件内容
        :param subtype: 邮件格式(例如：plain/html/json等)，默认html
        :param charset: 邮件字符编码
        :param filepath: 附件路径
        :param filename: 附件名字(默认：路径后缀)
        :param level: 报警等级
        :return:
        """
        try:
            if filepath:
                msg = MIMEMultipart()
                file = MIMEText(str(open(filepath, 'rb').read()), 'base64', 'utf-8')
                file["Content-Type"] = 'application/octet-stream'
                file["Content-Disposition"] = f'attachment; filename="{filename or filepath.split("/")[-1]}"'
                msg.attach(MIMEText(content, subtype, charset))
                msg.attach(file)
            else:
                msg = MIMEText(content, subtype, charset)

            msg['From'] = formataddr((self.mail_config['nickname'], self.mail_config['account']))
            if self.receivers is not None:
                msg['To'] = ','.join(self.receivers)
            if self.cc_receivers is not None:
                msg['CC'] = ','.join(self.cc_receivers)
            msg['Subject'] = level + subject

            # 腾讯企业邮箱发送邮件服务器 smtp.exmail.qq.com
            # qq邮箱发送邮件服务器  smtp.qq.com
            server = smtplib.SMTP_SSL(self.mail_config['mail_server'], self.mail_config['mail_port'])
            server.login(self.mail_config['account'], self.mail_config['password'])
            server.sendmail(self.mail_config['account'], self.receivers, msg.as_string())
            server.quit()
            Log().get_logger().info('邮件发送成功')
            return True
        except Exception as e:
            # 发送邮件失败，不能影响调用方，这个异常需要捕获
            Log().get_logger().exception(e)
            return False

    def warn(self, *args, **kwargs):
        self.__send_mail(level='[WARN]', *args, **kwargs)

    def info(self, *args, **kwargs):
        self.__send_mail(level='[INFO]', *args, **kwargs)

    def error(self, *args, **kwargs):
        self.__send_mail(level='[ERROR]', *args, **kwargs)
