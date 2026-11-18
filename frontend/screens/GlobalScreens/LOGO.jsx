import React from 'react';
import { Image, StyleSheet, View } from 'react-native';

const LOGO = ({ width, height }) => (
  <View>
    <Image
      source={require('../../assets/logo.png')}
      resizeMode="contain"
      style={{
        width,
        height,
      }}
    />
  </View>
);

export default LOGO;

const styles = StyleSheet.create({});
